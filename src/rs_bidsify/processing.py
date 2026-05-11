import logging

from pathlib import Path

from mne.io import BaseRaw
from mne_bids import BIDSPath

from rs_bidsify import data_io, update_dataset
from rs_bidsify.logging import setup_logging
from rs_bidsify.config import PARTICIPANT_INFO as part_info, PHENOTYPE_INFO as phen_info
from rs_bidsify.validation.description import DatasetDescription, AuxChanSpec
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
    participant_data = data_io.read_description_spreadsheet(
        sheet_path, part_info, "participant"
    )
    phenotype_data = data_io.read_description_spreadsheet(
        sheet_path, phen_info, "phenotype"
    )

    return DatasetDescription(
        spec=dataset_spec, participants=participant_data, phenotype=phenotype_data
    )


def process_recording(
    out_root_path: Path, recording: RecordingMetadata, dataset_desc: DatasetDescription
):

    logger.info(
        f"Processing Recording - Sub: {recording.subject}, Task: {recording.condition}, Session: {recording.session}"
    )

    eeg_data = data_io.read_eeg_recording(recording.path)

    subject_info = update_dataset.get_subject_info(
        recording, dataset_desc.participants["dataset"]
    )
    update_dataset.set_subject_info(eeg_data, subject_info)

    within_mne_updates(eeg_data, dataset_desc)

    rec_bids_path = data_io.write_bids(out_root_path, eeg_data, recording)

def within_mne_updates(eeg_data: BaseRaw, dataset_desc: DatasetDescription):
    """Update metadata that can placed in MNE objects and saved using MNE-BIDS"""
    acquisition_spec = dataset_desc.spec.acquisition_spec
    update_dataset.set_line_frequency(eeg_data, acquisition_spec)
    update_dataset.set_aux_channel_types(eeg_data, acquisition_spec.aux_channels)
    update_dataset.set_electrode_montage(eeg_data, acquisition_spec.eeg_channels)
    update_dataset.set_events(eeg_data, dataset_desc.spec.resting_state.events)


def enrich_eeg_sidecar(
    rec_bids_path: BIDSPath, dataset_desc: DatasetDescription, add_extras: bool = True
):
    """Enrich the eeg sidecar with information from the metadata that cannot be saved directly using MNE-BIDS"""

    entries_dict = {}
    acquisition_spec = dataset_desc.spec.acquisition_spec

    update_dataset.set_reference_chan(entries_dict, acquisition_spec)
    update_dataset.set_ground_chan(entries_dict, acquisition_spec)
    update_dataset.set_hardware_filters(entries_dict, acquisition_spec.filters)
    update_dataset.set_software_filters(entries_dict, acquisition_spec.filters)
    update_dataset.set_device_info(entries_dict, acquisition_spec)
    update_dataset.set_institution_info(entries_dict, dataset_desc.spec.metadata)

    if add_extras:
        update_dataset.set_extras(entries_dict, acquisition_spec)

    data_io.write_enriched_sidecar(rec_bids_path, entries_dict)


def enrich_channel_tsv(rec_bids_path: BIDSPath, channel_info: dict[str, AuxChanSpec]):
    """Enrich the channel tsv file with information from the metadata"""

    channel_tsv_path = rec_bids_path.copy().update(suffix="channels", extension="tsv")

    channel_tsv = data_io.read_bids_tsv(channel_tsv_path)
    update_dataset.set_channels_tsv(channel_info, channel_tsv)
    data_io.write_bids_tsv(channel_tsv_path, channel_tsv)

    logger.info(f"Updated channel tsv written to {channel_tsv_path}")
