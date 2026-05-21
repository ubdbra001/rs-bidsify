import logging
from pathlib import Path
from typing import Any

from mne.io import BaseRaw
from mne.channels import get_builtin_montages
from mne_bids import BIDSPath, make_dataset_description
from pandas import DataFrame, isna

from rs_bidsify.validation.description import (
    AcquisitionSpecs,
    AuxChanSpec,
    EEGChanSpec,
    ExtraSpec,
    DatasetMetadata,
    FilterSpec,
    FilterTypeOptions,
)
from rs_bidsify import io
from rs_bidsify.consistency import check_mapping_alignment
from rs_bidsify.validation.description import DescriptionSpec
from rs_bidsify.validation.subject import SubjectMetadata

logger = logging.getLogger(__name__)


def set_line_frequency(eeg_data: BaseRaw, acqusition_spec: AcquisitionSpecs):
    """Set the frequency for line noise"""
    eeg_data.info["line_freq"] = acqusition_spec.power_line_freq
    logger.info(f"Set line_freq to {acqusition_spec.power_line_freq} Hz")


def set_events(eeg_data: BaseRaw, event_info: dict[str, str]):
    """Set the events in the Recording"""

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
    """Set the types for the Aux Channels"""

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

    logger.warning("No valid channels found to update")


def set_electrode_montage(eeg_data: BaseRaw, eeg_spec: EEGChanSpec):
    """Set the electrode montage for the recording"""

    montage_info = eeg_spec.montage
    mne_montages = get_builtin_montages()

    if montage_info.mne_name is not None and montage_info.mne_name in mne_montages:
        eeg_data.set_montage(montage_info.mne_name)
        logger.info(f"Set EEG montage to built-in mne montage: {montage_info.mne_name}")
    elif montage_info.path is not None:
        # This should load the custom locations file and set the montage using it.
        # .lay files appear to be 2d while MNE expects Montages to be 3D, need to double check this
        pass
    else:
        # No valid montage information passed (mne_name doesn't match a valid built-in and no path provided)
        raise ValueError(
            "No valid montage infomation passed, please check the information provided"
        )


def set_subject_info(eeg_data: BaseRaw, subject_model: SubjectMetadata):
    """Set the information about the subject"""

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
    """Set the hardware filters used in the recording"""

    bids_key = "HardwareFilters"

    hw_filters = get_filters(filter_list, FilterTypeOptions.HARDWARE)
    set_filters(entries_dict, hw_filters, bids_key)


def set_software_filters(entries_dict: dict[str, Any], filter_list: list[FilterSpec]):
    """Set the software filters used in the recording"""

    bids_key = "SoftwareFilters"

    sw_filters = get_filters(filter_list, FilterTypeOptions.SOFTWARE)
    set_filters(entries_dict, sw_filters, bids_key)


def get_filters(
    filter_list: list[FilterSpec], filter_type: FilterTypeOptions
) -> dict[str, Any]:
    """Generic function for finding filters of specific type"""
    return {f.name: f.info for f in filter_list if f.type == filter_type}


def set_filters(entries_dict: dict[str, Any], filters: dict[str, Any], bids_key: str):
    """Set the filters in the update dictionary"""
    if filters:
        entries_dict.update({bids_key: filters})
        logger.info(f"Queued update - {bids_key}: {','.join(filters.keys())}")


def set_reference_chan(entries_dict: dict[str, Any], eeg_chan_spec: EEGChanSpec):
    """Set the reference channel"""

    mapping = {"EEGReference": "reference"}
    map_spec_to_bids(eeg_chan_spec, mapping, entries_dict)


def set_ground_chan(entries_dict: dict[str, Any], eeg_chan_spec: EEGChanSpec):
    """Set the ground channel"""

    mapping = {"EEGGround": "ground"}
    map_spec_to_bids(eeg_chan_spec, mapping, entries_dict)


def set_device_info(entries_dict: dict[str, Any], acquisition_spec: AcquisitionSpecs):

    mapping = {
        "ManufacturersModelName": "amplifier_model",
        "SoftwareVersions": "software",
    }
    map_spec_to_bids(acquisition_spec, mapping, entries_dict)


def set_institution_info(entries_dict: dict[str, Any], metadata: DatasetMetadata):
    """Set the institution name and dept"""

    mapping = {
        "InstitutionName": "institution_name",
        "InstitutionalDepartmentName": "institution_dept",
    }
    map_spec_to_bids(metadata, mapping, entries_dict)


def set_extras(entries_dict: dict[str, Any], extra_spec: ExtraSpec):
    """Set extra metadata not typically recorded in BIDS"""

    mapping = {
        "AcceptableImpedence": "acceptable_impedance",
        "ConductiveMedium": "conductive_medium",
        "FaradayCage": "faraday_cage",
        "SoundProofing": "sound_proof",
        "LightingConditions": "lighting_conditions",
    }

    map_spec_to_bids(extra_spec, mapping, entries_dict)


def map_spec_to_bids(source_obj: Any, mapping: dict[str, str], updates: dict[str, Any]):
    """Generic function that maps the data in metadata models to specific BIDS keys ready
    to be written to a sidecar file"""
    model_dict = source_obj.model_dump(include=set(mapping.values()), exclude_none=True)

    for bids_key, metadata_key in mapping.items():
        # Only add to the dictionary if a value actually exists
        if (val := model_dict.get(metadata_key, None)) is not None:
            updates[bids_key] = val
            logger.info(f"Queued update - {bids_key}: {val}")


def set_channels_tsv(channels: dict[str, AuxChanSpec], channel_tsv: DataFrame):
    """Update the existing channel information using metadata"""

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
    """Update the existing dataset description with additional supplied metadata"""
    make_dataset_description(
        path=out_root_path, **metadata.create_dict(), overwrite=True
    )


def enrich_mne_object(eeg_data: BaseRaw, dataset_spec: DescriptionSpec):
    """Update metadata that can placed in MNE objects and saved using MNE-BIDS"""
    acquisition_spec = dataset_spec.acquisition_spec
    set_line_frequency(eeg_data, acquisition_spec)
    set_aux_channel_types(eeg_data, acquisition_spec.aux_channels)
    set_electrode_montage(eeg_data, acquisition_spec.eeg_channels)
    set_events(eeg_data, dataset_spec.resting_state.events)


def enrich_eeg_sidecar(
    rec_bids_path: BIDSPath, dataset_spec: DescriptionSpec, add_extras: bool = True
):
    """Enrich the eeg sidecar with information from the metadata that cannot be saved directly using MNE-BIDS"""

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


def enrich_channel_tsv(rec_bids_path: BIDSPath, channel_info: dict[str, AuxChanSpec]):
    """Enrich the channel tsv file with information from the metadata"""

    channel_tsv_path = rec_bids_path.copy().update(suffix="channels", extension="tsv")

    channel_tsv = io.read_bids_tsv(channel_tsv_path)
    set_channels_tsv(channel_info, channel_tsv)
    io.write_bids_tsv(channel_tsv_path, channel_tsv)

    logger.info(f"Updated channel tsv written to {channel_tsv_path}")
