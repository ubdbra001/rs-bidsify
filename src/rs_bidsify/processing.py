import logging
from pathlib import Path

from rs_bidsify import data_io, update_dataset
from rs_bidsify.logging import setup_logging
from rs_bidsify.config import PARTICIPANT_INFO as part_info, PHENOTYPE_INFO as phen_info
from rs_bidsify.validation.description import DatasetDescription
from rs_bidsify.validation.dataset import EEGDatasetCrawler, RecordingMetadata
from rs_bidsify.utils import find_file

logger = logging.getLogger(__name__)

def process_dataset(raw_path: Path, out_root_path: Path):

    log_path = raw_path.parent / "logs"
    setup_logging(log_path)

    dataset_desc = generate_dataset_description(raw_path)

    crawler = EEGDatasetCrawler(
        root_path=raw_path,
        **dataset_desc.crawler_info
    )

def generate_dataset_description(root_path: Path):

    json_path = find_file(root_path, "json")
    sheet_path = find_file(root_path, "ods")

    dataset_spec = data_io.read_description_json(json_path)
    participant_data = data_io.read_description_spreadsheet(sheet_path, part_info, "participant")
    phenotype_data = data_io.read_description_spreadsheet(sheet_path, phen_info, "phenotype")

    return DatasetDescription(spec=dataset_spec, participants=participant_data, phenotype=phenotype_data)

def process_recording(out_root_path: Path, recording: RecordingMetadata, dataset_desc: DatasetDescription):
    
    logger.info(f"Processing Recording - Sub: {recording.subject}, Task: {recording.condition}, Session: {recording.session}")
                
    eeg_data = data_io.read_eeg_recording(recording.path)

    subject_info = update_dataset.get_subject_info(recording, dataset_desc.participants["dataset"])
    update_dataset.set_subject_info(eeg_data, subject_info)

    within_mne_updates(eeg_data, dataset_desc)

def within_mne_updates(eeg_data: BaseRaw, dataset_desc: DatasetDescription):
    """Update metadata that can placed in MNE objects and saved using MNE-BIDS"""
    acquisition_spec = dataset_desc.spec.acquisition_spec
    update_dataset.set_line_frequency(eeg_data, acquisition_spec)
    update_dataset.set_aux_channel_types(eeg_data, acquisition_spec.aux_channels)
    update_dataset.set_electrode_montage(eeg_data, acquisition_spec.eeg_channels)
    update_dataset.set_events(eeg_data, dataset_desc.spec.resting_state.events)

