import logging
from pathlib import Path
from typing import Any

from mne.io import BaseRaw
from mne_bids import BIDSPath, make_dataset_description
from pandas import DataFrame, isna

from rs_bidsify import io
from rs_bidsify.consistency import check_mapping_alignment
from rs_bidsify.validation.description import (
    AcquisitionSpecs,
    AuxChanSpec,
    DatasetMetadata,
    DescriptionSpec,
    EEGChanSpec,
    ExtraSpec,
    FilterSpec,
    FilterTypeOptions,
)
from rs_bidsify.validation.subject import SubjectMetadata

logger = logging.getLogger(__name__)


def set_line_frequency(eeg_data: BaseRaw, acqusition_spec: AcquisitionSpecs):
    """
    Set the power line frequency in the MNE Raw object info.

    Updates the `line_freq` attribute of the recording metadata based on
    the provided acquisition specifications. This value is essential for
    artifact removal and BIDS sidecar generation.

    Parameters
    ----------
    eeg_data : BaseRaw
        The MNE Raw object to be updated.
    acqusition_spec : AcquisitionSpecs
        Specification object containing the `power_line_freq` value.

    Returns
    -------
    None
        Updates the `eeg_data` object in-place.
    """
    eeg_data.info["line_freq"] = acqusition_spec.power_line_freq
    logger.info(f"Set line_freq to {acqusition_spec.power_line_freq} Hz")


def set_events(eeg_data: BaseRaw, event_info: dict[str, str]):
    """
    Map raw EEG trigger descriptions to BIDS-compliant event labels.

    Synchronizes recording annotations with user metadata. Only triggers
    found in both the file and the metadata are renamed.

    Parameters
    ----------
    eeg_data : BaseRaw
        The MNE Raw object containing raw annotations.
    event_info : dict[str, str]
        A mapping of {raw_trigger_name: bids_event_label} form the metadata.

    Returns
    -------
    None
        Updates the `eeg_data.annotations` in-place.

    Notes
    -----
    This function uses strict symmetry. It will log a warning if:
    1. A trigger defined in your metadata is missing from the EEG file.
    2. A trigger found in the EEG file is missing from your metadata.
    """
    valid_events = check_mapping_alignment(
        actual=eeg_data.annotations.description,
        expected=event_info,
        context="Events",
        strict_symmetry=True,
    )

    if valid_events:
        eeg_data.annotations.rename(valid_events)

        ev_updates = ", ".join([f"{k} -> {v}" for k, v in valid_events.items()])
        logger.info(f"Events renamed: {ev_updates}")


def set_aux_channel_types(eeg_data: BaseRaw, aux_chans: dict[str, AuxChanSpec]):
    """
    Assign specific MNE channel types to auxiliary channels in the recording.

    Converts auxiliary channel specifications from metadata into an MNE-compatible
    type map. It identifies which of the specified channels exist in the
    current recording and updates their types in-place.

    Parameters
    ----------
    eeg_data : BaseRaw
        The MNE Raw object whose channel types need to be updated.
    aux_chans : dict[str, AuxChanSpec]
        A mapping of channel names to their specifications, including the
        expected MNE channel type.

    Returns
    -------
    None
        Updates the `eeg_data` object in-place and logs the changes.
    """
    type_map = {k: v.mne_type.value for k, v in aux_chans.items()}

    valid_chans = check_mapping_alignment(
        actual=eeg_data.ch_names,
        expected=type_map,
        context="Aux Channels",
        strict_symmetry=False,
    )

    if valid_chans:
        eeg_data.set_channel_types(valid_chans)

        ch_updates = ", ".join([f"{k} - {v}" for k, v in valid_chans.items()])
        logger.info(f"Specified Aux channel MNE types set: {ch_updates}")
    else:
        logger.warning("No valid channels found to update")


def set_electrode_montage(eeg_data: BaseRaw, eeg_spec: EEGChanSpec):
    """
    Apply a physical electrode coordinate system (montage) to the EEG data.

    Utilizes the pre-validated montage configuration from the EEG specification
    to assign 3D sensor locations to the MNE Raw object.

    Parameters
    ----------
    eeg_data : BaseRaw
        The MNE Raw object to which the montage will be applied.
    eeg_spec : EEGChanSpec
        The EEG channel specification containing the resolved Montage model.

    Returns
    -------
    None
        The `eeg_data` object is modified in-place.

    Raises
    ------
    Exception
        Re-raises any exception encountered during montage application,
        typically due to channel name mismatches between the data and montage.
    """
    montage_info = eeg_spec.montage

    try:
        eeg_data.set_montage(montage_info.montage)
        source = montage_info.mne_name or montage_info.path
        logger.info(f"Successfully applied montage from source: {source}")
    except Exception as e:
        logger.error(f"failed to apply montage {e}")
        raise


def set_subject_info(eeg_data: BaseRaw, subject_model: SubjectMetadata):
    """
    Populate the MNE Raw object with participant demographic information.

    Updates the `info['subject_info']` dictionary using data from the
    SubjectMetadata model. This handles cases where subject information
    is entirely missing or needs to be merged with existing entries.

    Parameters
    ----------
    eeg_data : BaseRaw
        The MNE Raw object to be updated.
    subject_model : SubjectMetadata
        The model containing subject details, providing an MNE-compatible
        dictionary via `subject_info_dump()`.

    Returns
    -------
    None
        Updates the `eeg_data` object in-place and logs the update.
    """
    if eeg_data.info.get("subject_info") is None:
        eeg_data.info["subject_info"] = subject_model.subject_info_dump()
    elif isinstance(eeg_data.info["subject_info"], dict):
        eeg_data.info["subject_info"].update(subject_model.subject_info_dump())
    else:
        # may want to raise a warning here if there is something in
        # subject_info, but it is not of an expected type
        pass

    logger.info(f"Updated subject information: {subject_model}")


def set_hardware_filters(entries_dict: dict[str, Any], filter_list: list[FilterSpec]):
    """
    Identify and queue hardware filters for the BIDS sidecar update.

    Filters the provided list for hardware-specific entries and adds them
    to the entries dictionary under the 'HardwareFilters' key.

    Parameters
    ----------
    entries_dict : dict[str, Any]
        The dictionary containing pending updates for the BIDS JSON sidecar.
    filter_list : list[FilterSpec]
        A collection of filter specifications containing both hardware
        and software filters.

    Returns
    -------
    None
        Updates the `entries_dict` in-place.
    """
    bids_key = "HardwareFilters"

    hw_filters = get_filters(filter_list, FilterTypeOptions.HARDWARE)
    set_filters(entries_dict, hw_filters, bids_key)


def set_software_filters(entries_dict: dict[str, Any], filter_list: list[FilterSpec]):
    """
    Identify and queue software filters for the BIDS sidecar update.

    Filters the provided list for software-specific entries and adds them
    to the entries dictionary under the 'SoftwareFilters' key.

    Parameters
    ----------
    entries_dict : dict[str, Any]
        The dictionary containing pending updates for the BIDS JSON sidecar.
    filter_list : list[FilterSpec]
        A collection of filter specifications containing both hardware
        and software filters.

    Returns
    -------
    None
        Updates the `entries_dict` in-place.
    """
    bids_key = "SoftwareFilters"

    sw_filters = get_filters(filter_list, FilterTypeOptions.SOFTWARE)
    set_filters(entries_dict, sw_filters, bids_key)


def get_filters(filter_list: list[FilterSpec], filter_type: FilterTypeOptions) -> dict[str, Any]:
    """
    Extract filters of a specific type from a list of specifications.

    Parameters
    ----------
    filter_list : list[FilterSpec]
        The list of filters to search through.
    filter_type : FilterTypeOptions
        The category of filter to retrieve (e.g., HARDWARE or SOFTWARE).

    Returns
    -------
    dict[str, Any]
        A mapping of filter names to their descriptive information.
    """
    return {f.name: f.info for f in filter_list if f.type == filter_type}


def set_filters(entries_dict: dict[str, Any], filters: dict[str, Any], bids_key: str):
    """
    Update the sidecar dictionary with identified filters.

    Parameters
    ----------
    entries_dict : dict[str, Any]
        The dictionary used for the final JSON update.
    filters : dict[str, Any]
        The filtered mapping of filter names and info to be added.
    bids_key : str
        The specific BIDS field name to update.

    Returns
    -------
    None
        Updates the `entries_dict` in-place.
    """
    if filters:
        entries_dict.update({bids_key: filters})
        logger.info(f"Queued update - {bids_key}: {','.join(filters.keys())}")


def set_reference_chan(entries_dict: dict[str, Any], eeg_chan_spec: EEGChanSpec):
    """
    Map the EEG reference channel information to the BIDS metadata.

    Identifies the reference channel from the EEG specification and queues it
    for the sidecar update under the 'EEGReference' key.

    Parameters
    ----------
    entries_dict : dict[str, Any]
        The dictionary containing pending updates for the BIDS JSON sidecar.
    eeg_chan_spec : EEGChanSpec
        The channel specification containing the reference channel details.

    Returns
    -------
    None
        Updates the `entries_dict` in-place.
    """
    mapping = {"EEGReference": "reference"}
    map_spec_to_bids(eeg_chan_spec, mapping, entries_dict)


def set_ground_chan(entries_dict: dict[str, Any], eeg_chan_spec: EEGChanSpec):
    """
    Map the EEG ground channel information to the BIDS metadata.

    Identifies the ground channel from the EEG specification and queues it
    for the sidecar update under the 'EEGGround' key.

    Parameters
    ----------
    entries_dict : dict[str, Any]
        The dictionary containing pending updates for the BIDS JSON sidecar.
    eeg_chan_spec : EEGChanSpec
        The channel specification containing the ground channel details.

    Returns
    -------
    None
        Updates the `entries_dict` in-place.
    """
    mapping = {"EEGGround": "ground"}
    map_spec_to_bids(eeg_chan_spec, mapping, entries_dict)


def set_device_info(entries_dict: dict[str, Any], acquisition_spec: AcquisitionSpecs):
    """
    Map hardware and acquisition software details to BIDS metadata.

    Identifies the amplifier model and software versions from the acquisition
    specification and queues them for the sidecar update.

    Parameters
    ----------
    entries_dict : dict[str, Any]
        The dictionary containing pending updates for the BIDS JSON sidecar.
    acquisition_spec : AcquisitionSpecs
        The specification containing amplifier and software details.

    Returns
    -------
    None
        Updates the `entries_dict` in-place.
    """
    mapping = {
        "ManufacturersModelName": "amplifier_model",
        "SoftwareVersions": "software",
    }
    map_spec_to_bids(acquisition_spec, mapping, entries_dict)


def set_institution_info(entries_dict: dict[str, Any], metadata: DatasetMetadata):
    """
    Map institutional and departmental details to BIDS metadata.

    Identifies the institution name and department from the dataset metadata
    and queues them for the sidecar update.

    Parameters
    ----------
    entries_dict : dict[str, Any]
        The dictionary containing pending updates for the BIDS JSON sidecar.
    metadata : DatasetMetadata
        The global dataset metadata containing institutional information.

    Returns
    -------
    None
        Updates the `entries_dict` in-place.
    """
    mapping = {
        "InstitutionName": "institution_name",
        "InstitutionalDepartmentName": "institution_dept",
    }
    map_spec_to_bids(metadata, mapping, entries_dict)


def set_extras(entries_dict: dict[str, Any], extra_spec: ExtraSpec):
    """
    Map supplemental environmental and recording details to BIDS metadata.

    Identifies non-standard BIDS fields—such as impedance thresholds, room
    shielding, and lighting—from the extra specification and queues them
    for the sidecar update.

    Parameters
    ----------
    entries_dict : dict[str, Any]
        The dictionary containing pending updates for the BIDS JSON sidecar.
    extra_spec : ExtraSpec
        The specification containing environmental and setup details.

    Returns
    -------
    None
        Updates the `entries_dict` in-place.
    """
    mapping = {
        "AcceptableImpedence": "acceptable_impedance",
        "ConductiveMedium": "conductive_medium",
        "FaradayCage": "faraday_cage",
        "SoundProofing": "sound_proof",
        "LightingConditions": "lighting_conditions",
    }

    map_spec_to_bids(extra_spec, mapping, entries_dict)


def map_spec_to_bids(source_obj: Any, mapping: dict[str, str], updates: dict[str, Any]):
    """
    Map attributes from a metadata model to BIDS-compliant sidecar keys.

    Extracts specific values from a source specification object based on a
    provided mapping dictionary. It filters for non-null values and prepares
    them for inclusion in the BIDS JSON sidecar.

    Parameters
    ----------
    source_obj : Any
        The metadata model (typically a Pydantic object) containing the data.
    mapping : dict[str, str]
        A dictionary where keys are the target BIDS fields and values are
        the attribute names in the `source_obj`.
    updates : dict[str, Any]
        The dictionary containing pending updates for the BIDS JSON sidecar.

    Returns
    -------
    None
        Updates the `updates` dictionary in-place.
    """
    model_dict = source_obj.model_dump(include=set(mapping.values()), exclude_none=True)

    for bids_key, metadata_key in mapping.items():
        # Only add to the dictionary if a value actually exists
        if (val := model_dict.get(metadata_key, None)) is not None:
            updates[bids_key] = val
            logger.info(f"Queued update - {bids_key}: {val}")


def set_channels_tsv(channels: dict[str, AuxChanSpec], channel_tsv: DataFrame):
    """
    Update the channel metadata table with BIDS-specific details.

    Synchronizes the tabular channel data with provided specifications. It
    prioritizes updating 'MISC' types to specific BIDS types, adding
    channel descriptions, and filling in missing unit information.

    Parameters
    ----------
    channels : dict[str, AuxChanSpec]
        A mapping of channel names to their detailed specifications.
    channel_tsv : DataFrame
        The pandas DataFrame representing the contents of the channels.tsv file,
        indexed by channel name.

    Returns
    -------
    None
        Updates the `channel_tsv` DataFrame in-place.
    """
    valid_keys = set(channels.keys()).intersection(channel_tsv.index)

    for chan in valid_keys:
        info = channels[chan]

        if info.bids_type is not None and channel_tsv.loc[chan, "type"] == "MISC":
            channel_tsv.loc[chan, "type"] = info.bids_type.value

            logger.info(f"Updated type for {chan} to {info.bids_type.value}")
            if info.description is not None:
                channel_tsv.loc[chan, "description"] = info.description

        if info.units is not None and isna(channel_tsv.loc[chan, "units"]):
            channel_tsv.loc[chan, "units"] = info.units
            logger.info(f"Updated units for {chan} to {info.units}")


def enrich_dataset_description(metadata: DatasetMetadata, out_root_path: Path):
    """
    Update the top-level BIDS dataset description file.

    Identifies the dataset metadata from the provided model and writes it
    to the `dataset_description.json` file at the output root. This ensures
    the project-wide metadata matches the supplied specification.

    Parameters
    ----------
    metadata : DatasetMetadata
        The global metadata model containing dataset details like Name,
        BIDSVersion, and Authors.
    out_root_path : Path
        The root directory of the BIDS dataset where the description
        file is located.

    Returns
    -------
    None
        Writes or overwrites the `dataset_description.json` file on disk.
    """
    make_dataset_description(path=out_root_path, **metadata.create_dict(), overwrite=True)


def enrich_mne_object(eeg_data: BaseRaw, dataset_spec: DescriptionSpec):
    """
    Update MNE Raw object metadata with experimental and acquisition details.

    Orchestrates the enrichment of the recording by applying line frequency,
    auxiliary channel types, electrode montages, and event markers. This
    ensures the MNE object is fully specified before being saved via MNE-BIDS.

    Parameters
    ----------
    eeg_data : BaseRaw
        The MNE Raw object to be enriched.
    dataset_spec : DescriptionSpec
        The comprehensive dataset specification containing acquisition and
        event details.

    Returns
    -------
    None
        Updates the `eeg_data` object in-place.
    """
    acquisition_spec = dataset_spec.acquisition_spec
    set_line_frequency(eeg_data, acquisition_spec)
    set_aux_channel_types(eeg_data, acquisition_spec.aux_channels)
    set_electrode_montage(eeg_data, acquisition_spec.eeg_channels)
    set_events(eeg_data, dataset_spec.resting_state.events)


def enrich_eeg_sidecar(rec_bids_path: BIDSPath, dataset_spec: DescriptionSpec, add_extras: bool = True):
    """
    Enrich the BIDS EEG sidecar with metadata not captured by standard MNE-BIDS.

    Orchestrates the extraction of reference/ground channels, filter specs,
    hardware info, and institutional details into an entries dictionary. This
    dictionary is then written to the existing JSON sidecar file.

    Parameters
    ----------
    rec_bids_path : BIDSPath
        The MNE-BIDS path object pointing to the recording's sidecar file.
    dataset_spec : DescriptionSpec
        The comprehensive dataset specification containing acquisition details.
    add_extras : bool, default True
        If True, includes supplemental environmental and recording conditions
        (e.g., lighting, impedance) in the sidecar.

    Returns
    -------
    None
        Writes the accumulated metadata to the JSON sidecar file on disk.
    """
    entries_dict = {}
    acquisition_spec = dataset_spec.acquisition_spec

    set_reference_chan(entries_dict, acquisition_spec.eeg_channels)
    set_ground_chan(entries_dict, acquisition_spec.eeg_channels)
    set_hardware_filters(entries_dict, acquisition_spec.filters)
    set_software_filters(entries_dict, acquisition_spec.filters)
    set_device_info(entries_dict, acquisition_spec)
    set_institution_info(entries_dict, dataset_spec.metadata)

    if acquisition_spec.extras is not None and add_extras:
        set_extras(entries_dict, acquisition_spec.extras)

    io.write_enriched_sidecar(rec_bids_path, entries_dict)


def enrich_channels_tsv_with_aux(rec_bids_path: BIDSPath, aux_info: dict[str, AuxChanSpec]):
    """
    Update the recording's channels.tsv file using auxiliary channel specifications.

    Reads the existing channel table from disk and applies metadata for auxiliary
    channels (e.g., ECG, EOG, or TRIG). This is primarily used to correct
    generic 'MISC' types and provide specific units and descriptions that
    MNE-BIDS does not automatically detect.

    Parameters
    ----------
    rec_bids_path : BIDSPath
        The MNE-BIDS path object used to locate the specific channels.tsv file.
    aux_info : dict[str, AuxChanSpec]
        A mapping of channel names to their auxiliary specifications.

    Returns
    -------
    None
        Reads from and writes to the channels.tsv file on disk.
    """
    channel_tsv_path = rec_bids_path.copy().update(suffix="channels", extension="tsv")

    channel_tsv = io.read_bids_tsv(channel_tsv_path)
    set_channels_tsv(aux_info, channel_tsv)
    io.write_bids_tsv(channel_tsv_path, channel_tsv)

    logger.info(f"Updated channel tsv written to {channel_tsv_path}")
