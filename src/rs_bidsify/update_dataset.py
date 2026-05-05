import logging
from mne.io import BaseRaw
from pandas import DataFrame
from rs_bidsify.validation.dataset import RecordingMetadata
from rs_bidsify.validation.description import AcquisitionSpecs
from rs_bidsify.validation.subject import SubjectMetadata

logger = logging.getLogger(__name__)

def set_line_frequency(eeg_data: BaseRaw, acqusition_spec: AcquisitionSpecs):
    """Set the frequency for line noise"""
    eeg_data.info["line_freq"] = acqusition_spec.power_line_freq
    logger.info(f"Set line_freq to {acqusition_spec.power_line_freq} Hz")


def get_subject_info(recording: RecordingMetadata, participants_df: DataFrame) -> SubjectMetadata:

    part_id = recording.participant
    subject_info = participants_df.loc[part_id].to_dict()

    return SubjectMetadata(**subject_info) # type: ignore


def set_subject_info(eeg_data: BaseRaw, subject_model: SubjectMetadata):
    """Set the information about the subject"""

    if eeg_data.info["subject_info"] is None:
        eeg_data.info["subject_info"] = subject_model.model_dump()
    elif isinstance(eeg_data.info["subject_info"], dict):
        eeg_data.info["subject_info"].update(subject_model.model_dump())
    else:
        # may want to raise a warning here if there is something in
        # subject_info, but it is not of an expected type
        pass
    
    logger.info(f"Updated subject information: {subject_model}")

