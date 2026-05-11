import logging
from typing import Any

from mne.io import BaseRaw
from mne.channels import get_builtin_montages
from pandas import DataFrame

from rs_bidsify.validation.dataset import RecordingMetadata
from rs_bidsify.validation.description import AcquisitionSpecs, AuxChanSpec, EEGChanSpec, DatasetMetadata
from rs_bidsify.validation.subject import SubjectMetadata

logger = logging.getLogger(__name__)

def set_line_frequency(eeg_data: BaseRaw, acqusition_spec: AcquisitionSpecs):
    """Set the frequency for line noise"""
    eeg_data.info["line_freq"] = acqusition_spec.power_line_freq
    logger.info(f"Set line_freq to {acqusition_spec.power_line_freq} Hz")

def set_events(eeg_data: BaseRaw, event_info: dict[str, str]):
    """Set the events in the Recording"""

    rec_annotations = set(eeg_data.annotations.description)

    present_annotations = rec_annotations.intersection(event_info.keys())
    logger.info(f"Specified Events found in recording: {', '.join(present_annotations)}")

    if missing_events := set(event_info.keys()).difference(present_annotations):
        logger.warning(f"Events specified in metadata but not present in recording: {', '.join(missing_events)}")

    if extra_events := rec_annotations.difference(event_info.keys()):
        logger.warning(f"Events present in recording, but not specified in metadata: {', '.join(extra_events)}")

    update_events = {key: value for key, value in event_info.items() if key in present_annotations}

    eeg_data.annotations.rename(update_events)

    ev_updates = ", ".join([f"{k} -> {v}" for k, v in update_events.items()])
    logger.info(f"Events renamed: {ev_updates}")

def set_aux_channel_types(eeg_data: BaseRaw, aux_chans: dict[str, AuxChanSpec]):
    """Set the types for the Aux Channels"""

    aux_names = set(aux_chans.keys())

    present_chans = aux_names.intersection(eeg_data.ch_names)
    logger.info(f"Specified Aux channels found in recording: {', '.join(present_chans)}")

    if missing_chans := aux_names.difference(eeg_data.ch_names):
        logger.warning(f"Specified Aux channels not present in recording: {', '.join(missing_chans)}")

    chan_types = {key: val.mne_type.value for key, val in aux_chans.items() if key in present_chans}

    eeg_data.set_channel_types(chan_types)

    ch_updates = ", ".join([f"{k} - {v}" for k, v in chan_types.items()])
    logger.info(f"Specified Aux channel mne types set: {ch_updates}")



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
        # No valid montage infomation passed (mne_name doesn't match a valid built-in and no path provided)
        raise ValueError("No valid montage infomation passed, please check the information provided")

def get_subject_info(recording: RecordingMetadata, participants_df: DataFrame) -> SubjectMetadata:

    part_id = recording.participant
    subject_info = participants_df.loc[part_id].to_dict()

    return SubjectMetadata(**subject_info) # type: ignore


def set_subject_info(eeg_data: BaseRaw, subject_model: SubjectMetadata):
    """Set the information about the subject"""

    if eeg_data.info["subject_info"] is None:
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
    add_filters(entries_dict, hw_filters, bids_key)


def set_software_filters(entries_dict: dict[str, Any], filter_list: list[FilterSpec]):
    """Set the software filters used in the recording"""

    bids_key = "SoftwareFilters"

    sw_filters = get_filters(filter_list, FilterTypeOptions.SOFTWARE)
    add_filters(entries_dict, sw_filters, bids_key)


def get_filters(filter_list: list[FilterSpec], filter_type: FilterTypeOptions) -> dict[str, Any]:
    """Generic function for finding filters of specific type"""
    return {f.name: f.info for f in filter_list if f.type == filter_type}

def add_filters(entries_dict: dict[str, Any], filters: dict[str, Any], bids_key):
    """Set the filters in the update dictionary"""
    if filters:
        entries_dict.update({bids_key: filters})
        logger.info(f"Queued update - {bids_key}: {','.join(filters.keys())}")

def set_reference_chan(entries_dict: dict[str, Any], acquisition_spec: AcquisitionSpecs):
    """Set the reference channel"""

    mapping = {"EEGReference": "reference"}
    map_spec_to_bids(acquisition_spec.eeg_channels, mapping, entries_dict)

def set_ground_chan(entries_dict: dict[str, Any], acquisition_spec: AcquisitionSpecs):
    """Set the ground channel"""

    mapping = {"EEGGround": "ground"}
    map_spec_to_bids(acquisition_spec.eeg_channels, mapping, entries_dict)

def hardware_info(entries_dict: dict[str, Any], acquisition_spec: AcquisitionSpecs):

    mapping = {"ManufacturersModelName": "amplifier_model"}
    map_spec_to_bids(acquisition_spec, mapping, entries_dict)

def software_info(entries_dict: dict[str, Any], acquisition_spec: AcquisitionSpecs):

    mapping = {"SoftwareVersions": "software"}
    map_spec_to_bids(acquisition_spec, mapping, entries_dict)

def set_institution_info(entries_dict: dict[str, Any], metadata: DatasetMetadata):
    """Set the institution name and dept"""

    mapping = {
        "InstitutionName": "institution_name",
        "InstitutionalDepartmentName": "institution_dept" 
    }
    map_spec_to_bids(metadata, mapping, entries_dict)

def set_extras():

def map_spec_to_bids(source_obj: Any, mapping: dict[str, str], updates: dict[str, Any]):
    for bids_key, attr_name in mapping.items():
        val = getattr(source_obj, attr_name, None)
        
        # Only add to the dictionary if a value actually exists
        if val is not None:
            updates[bids_key] = val
            logger.info(f"Queued update - {bids_key}: {val}")