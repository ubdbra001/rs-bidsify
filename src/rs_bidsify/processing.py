import logging

from pathlib import Path

from rs_bidsify import enrichment, io, discovery
from rs_bidsify.logging import setup_logging
from rs_bidsify.validation.description import DescriptionSpec
from rs_bidsify.validation.dataset import EEGDatasetCrawler, RecordingMetadata
from rs_bidsify.validation.subject import SubjectMetadata
from rs_bidsify.utils import locate_dynamic_fields

logger = logging.getLogger(__name__)


def process_dataset(raw_path: Path, out_root_path: Path):
    """Main function for processing a dataset"""

    log_path = raw_path.parent / "logs"
    setup_logging(log_path)

    dataset_spec = discovery.find_description_spec(raw_path)
    participant_data, phenotype_data = discovery.find_dataset_spreadsheets(raw_path)

    dynamic_paths = locate_dynamic_fields(dataset_spec.model_dump())

    expected_participants = participant_data["dataset"].index.to_list()

    crawler = EEGDatasetCrawler(
        root_path=raw_path,
        expected_participants=expected_participants,
        **dataset_spec.crawler_info,
    )

    dataset_desc = (dataset_spec, participant_data)

    for recording in crawler.found_recordings:
        process_recording(out_root_path, recording, dataset_desc, dynamic_paths)

    enrichment.enrich_dataset_description(dataset_spec.metadata, out_root_path)
    io.write_phenotype_data(phenotype_data, out_root_path)


def process_recording(
    out_root_path: Path,
    recording: RecordingMetadata,
    dataset_desc: tuple[DescriptionSpec, dict],
    dynamic_paths: list,
):

    dataset_spec, participants = dataset_desc
    logger.info(
        f"Processing Recording - Sub: {recording.subject}, Task: {recording.condition}, Session: {recording.session}"
    )

    subject_info = SubjectMetadata.from_dataframe(recording, participants["dataset"])

    if dynamic_paths:
        subject_spec = DescriptionSpec.from_template(
            dataset_spec, dynamic_paths, subject_info
        )
    else:
        subject_spec = dataset_spec

    eeg_data = io.read_eeg_recording(recording.path)

    enrichment.set_subject_info(eeg_data, subject_info)

    enrichment.enrich_mne_object(eeg_data, subject_spec)

    rec_bids_path = io.write_bids(out_root_path, eeg_data, recording)

    enrichment.enrich_eeg_sidecar(rec_bids_path, subject_spec)
    enrichment.enrich_channel_tsv(
        rec_bids_path, subject_spec.acquisition_spec.aux_channels
    )
