import logging

from pathlib import Path

from rs_bidsify import enrichment, io, discovery
from rs_bidsify.config_loader import get_default_config, deep_merge
from rs_bidsify.validation.description import DescriptionSpec
from rs_bidsify.validation.dataset import EEGDatasetCrawler, RecordingMetadata
from rs_bidsify.validation.subject import SubjectMetadata
from rs_bidsify.utils import locate_dynamic_fields

logger = logging.getLogger(__name__)


def process_dataset(
    raw_path: Path, out_root_path: Path, config_override: dict | None = None
):
    """Main function for processing a dataset"""

    config = get_default_config()

    if config_override:
        config = deep_merge(config, config_override)

    dataset_spec = discovery.find_description_spec(
        raw_path, extension=config["metadata_ext"]
    )

    participant_data, phenotype_data = discovery.find_dataset_spreadsheets(
        raw_path, sheet_info=config["sheet_info"], extension=config["spreadsheet_ext"]
    )

    dynamic_paths = locate_dynamic_fields(dataset_spec.model_dump())

    expected_participants = participant_data["dataset"].index.to_list()

    crawler = EEGDatasetCrawler(
        root_path=raw_path,
        expected_participants=expected_participants,
        **dataset_spec.crawler_info,
    )

    rec_config = {k: config[k] for k in ("output_EEG_format", "include_extras")}
    for recording in crawler.found_recordings:
        subject_info = SubjectMetadata.from_dataframe(
            recording,
            participant_data["dataset"],
            mapping=config["demographic_mappings"],
        )
        process_recording(
            out_root_path,
            recording,
            dataset_spec,
            subject_info,
            dynamic_paths,
            rec_config,
        )

    enrichment.enrich_dataset_description(dataset_spec.metadata, out_root_path)
    if phenotype_data:
        io.write_phenotype_data(phenotype_data, out_root_path)


def process_recording(
    out_root_path: Path,
    recording: RecordingMetadata,
    dataset_spec: DescriptionSpec,
    subject_info: SubjectMetadata,
    dynamic_paths: list,
    config: dict,
):

    format = config["output_EEG_format"]
    include_extras = config["include_extras"]

    logger.info(
        f"Processing Recording - Sub: {recording.subject}, Task: {recording.condition}"
    )

    if dynamic_paths:
        subject_spec = DescriptionSpec.from_template(
            dataset_spec, dynamic_paths, subject_info
        )
    else:
        subject_spec = dataset_spec

    eeg_data = io.read_eeg_recording(recording.path)

    enrichment.set_subject_info(eeg_data, subject_info)

    enrichment.enrich_mne_object(eeg_data, subject_spec)

    rec_bids_path = io.write_bids(out_root_path, eeg_data, recording, format)

    enrichment.enrich_eeg_sidecar(rec_bids_path, subject_spec, include_extras)
    enrichment.enrich_channel_tsv(
        rec_bids_path, subject_spec.acquisition_spec.aux_channels
    )
