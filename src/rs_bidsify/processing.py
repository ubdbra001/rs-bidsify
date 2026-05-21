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
    """
    Orchestrate the conversion of a full raw dataset into BIDS format.

    This function manages the end-to-end workflow: merging configurations,
    discovering metadata, and crawling for EEG recordings. It assumes the
    source directory contains a valid metadata spreadsheet and description file.

    The process will automatically create the output BIDS directory if it
    does not exist and will overwrite existing files during the conversion.

    Parameters
    ----------
    raw_path : Path
        The directory containing the source raw data and metadata files.
    out_root_path : Path
        The destination directory where the BIDS structure will be built.
    config_override : dict, optional
        User-defined settings to override the default package configuration.

    Returns
    -------
    None
        Executes the conversion pipeline and writes the output to disk.
    """
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
    """
    Process and export a single recording instance to BIDS format.

    This function handles the transformation of an individual EEG file
    (one task/run). It specializes the dataset-level template for the
    specific subject, enriches the MNE object, and writes the resulting
    files to the BIDS structure. Post-export, it enriches the task-specific
    JSON sidecar and channels TSV.

    Parameters
    ----------
    out_root_path : Path
        The root directory of the BIDS dataset.
    recording : RecordingMetadata
        Metadata for this specific recording session (e.g., file path,
        subject ID, and task name).
    dataset_spec : DescriptionSpec
        The base metadata specification for the entire dataset.
    subject_info : SubjectMetadata
        Demographic and clinical metadata for the subject associated
        with this recording.
    dynamic_paths : list
        A list of keys within the metadata that should be dynamically
        populated using subject-specific values.
    config : dict
        Configuration settings, including 'output_EEG_format' and
        'include_extras'.

    Returns
    -------
    None
        Writes the processed recording and task-specific metadata to disk.
    """
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
    enrichment.enrich_channels_tsv_with_aux(
        rec_bids_path, subject_spec.acquisition_spec.aux_channels
    )
