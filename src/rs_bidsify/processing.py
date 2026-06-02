import logging
from dataclasses import dataclass
from pathlib import Path

from mne_bids import BIDSPath, write_raw_bids

from rs_bidsify import discovery, enrichment, io
from rs_bidsify.config_loader import deep_merge, get_default_config
from rs_bidsify.utils import locate_dynamic_fields
from rs_bidsify.validation.dataset import EEGDatasetCrawler, RecordingMetadata
from rs_bidsify.validation.description import DescriptionSpec
from rs_bidsify.validation.subject import SubjectMetadata

logger = logging.getLogger(__name__)


@dataclass
class RecordingPlan:
    """Holds a single recording paired with its pre-calculated subject specs."""

    recording: RecordingMetadata
    subject_info: SubjectMetadata
    subject_spec: DescriptionSpec

@dataclass
class DatasetPlan:
    """Holds the validated state and pre-calculated plans for the entire dataset."""

    dataset_spec: DescriptionSpec
    participant_data: dict
    phenotype_data: dict | None
    expected_participants: list
    recording_plans: list[RecordingPlan]


def process_metadata(
    raw_path: Path,
    config: dict,
) -> DatasetPlan:
    """Process metadata and return processing plan for dataset"""

    dataset_spec = discovery.find_description_spec(raw_path, extension=config["metadata_ext"])

    participant_data, phenotype_data = discovery.find_dataset_spreadsheets(
        raw_path, sheet_info=config["sheet_info"], extension=config["spreadsheet_ext"]
    )

    expected_participants = participant_data["dataset"].index.to_list()

    crawler = EEGDatasetCrawler(
        root_path=raw_path,
        expected_participants=expected_participants,
        **dataset_spec.crawler_info,
    )

    dynamic_paths = locate_dynamic_fields(dataset_spec.model_dump())

    recording_plans = []

    for recording in crawler.found_recordings:
        subject_info = SubjectMetadata.from_dataframe(
            recording,
            participant_data["dataset"],
            mapping=config["demographic_mappings"],
        )

        subject_spec = (
            DescriptionSpec.from_template(dataset_spec, dynamic_paths, subject_info)
            if dynamic_paths
            else dataset_spec
        )

        recording_plans.append(
            RecordingPlan(
                recording=recording,
                subject_info=subject_info,
                subject_spec=subject_spec
            )
        )
    
    return DatasetPlan(
        dataset_spec=dataset_spec,
        participant_data=participant_data,
        phenotype_data=phenotype_data,
        expected_participants=expected_participants,
        recording_plans=recording_plans
    )

def process_dataset(
    raw_path: Path,
    out_root_path: Path,
    config_override: dict | None = None,
    force_flag: bool = False,
    strict_flag: bool = False,
) -> list[dict]:
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

    dataset_spec = discovery.find_description_spec(raw_path, extension=config["metadata_ext"])

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

    results = []

    for recording in crawler.found_recordings:
        bids_path = BIDSPath(
            subject=recording.subject,
            task=recording.task,
            root=out_root_path,
        )

        if io.check_task_exists(bids_path.directory, recording.task) and not force_flag:
            logger.info(f"{recording.info_str} - Skipping as BIDSified files already exist")
            results.append({"recording": recording, "status": "Skipped", "error": ""})
            continue

        subject_info = SubjectMetadata.from_dataframe(
            recording,
            participant_data["dataset"],
            mapping=config["demographic_mappings"],
        )

        try:
            subject_spec = (
                DescriptionSpec.from_template(dataset_spec, dynamic_paths, subject_info)
                if dynamic_paths
                else dataset_spec
            )

            # Process recording
            process_recording(
                bids_path,
                recording,
                subject_spec,
                subject_info,
                rec_config,
            )

            results.append({"recording": recording, "status": "Success", "error": ""})
        except Exception as e:
            logger.exception(f"{recording.info_str} - Processing failed")

            io.rollback_recording_files(bids_path.directory, recording)

            if strict_flag:
                # Initial attempt
                # Remove "ghost" participants after strict crash
                if not bids_path.directory.exists():
                    io.cleanup_participants_tsv([recording.subject], out_root_path)
                raise

            results.append({"recording": recording, "status": "Failed", "error": str(e)})
            continue

    missing_subjects = discovery.find_missing_subjects(expected_participants, out_root_path)
    io.cleanup_participants_tsv(missing_subjects, out_root_path)
    enrichment.enrich_dataset_description(dataset_spec.metadata, out_root_path)

    if phenotype_data:
        io.write_phenotype_data(phenotype_data, out_root_path, missing_subjects)

    logger.info("Enriched BIDS-compliant dataset")

    return results


def process_recording(
    bids_path: BIDSPath,
    recording: RecordingMetadata,
    dataset_spec: DescriptionSpec,
    subject_info: SubjectMetadata,
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
    bids_path : BIDSPath
        The target BIDS destination for this recording. This object must specify
        the subject, task, and root directory, ensuring the data is written
        to the correct entity-linked location.
    recording : RecordingMetadata
        Metadata for this specific recording session (e.g., file path,
        subject ID, and task name).
    dataset_spec : DescriptionSpec
        The base metadata specification for the entire dataset.
    subject_info : SubjectMetadata
        Demographic and clinical metadata for the subject associated
        with this recording.
    config : dict
        Configuration settings, including 'output_EEG_format' and
        'include_extras'.

    Returns
    -------
    None
        Writes the processed recording and task-specific metadata to disk.
    """
    out_format = config["output_EEG_format"]
    include_extras = config["include_extras"]

    logger.info(f"{recording.info_str} - Processing Recording")

    eeg_data = io.read_eeg_recording(recording.path)

    enrichment.set_subject_info(eeg_data, subject_info)

    enrichment.enrich_mne_object(eeg_data, dataset_spec)

    rec_bids_path = write_raw_bids(eeg_data, bids_path, overwrite=True, allow_preload=True, format=out_format.upper())

    logger.info(f"{recording.info_str} - Saved BIDS-compliant data")

    enrichment.enrich_eeg_sidecar(rec_bids_path, dataset_spec, include_extras)
    enrichment.enrich_channels_tsv_with_aux(rec_bids_path, dataset_spec.acquisition_spec.aux_channels)

    logger.info(f"{recording.info_str} - Enriched BIDS-compliant data")
