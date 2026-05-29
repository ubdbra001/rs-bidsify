import logging
import shutil
from pathlib import Path
from typing import Any

import pandas as pd
from mne.io import BaseRaw, read_raw
from mne_bids import BIDSPath, update_sidecar_json

from rs_bidsify.utils import filter_dataframe_by_valid_ids, get_utc_today
from rs_bidsify.validation.dataset import RecordingMetadata
from rs_bidsify.validation.description import DescriptionSpec

logger = logging.getLogger(__name__)


def read_description_json(file_path: Path) -> DescriptionSpec:
    """
    Read and validate a dataset description JSON file.

    Loads the raw text from the specified path and parses it into a
    validated Pydantic model. Logs a confirmation message upon
    successful validation.

    Parameters
    ----------
    file_path : Path
        The path to the description JSON file to be read.

    Returns
    -------
    DescriptionSpec
        The validated data model containing the dataset description metadata.

    Notes
    -----
    This function utilizes Pydantic's `model_validate_json` for schema
    enforcement. If the JSON structure does not match `DescriptionSpec`,
    a validation error will be raised.
    """
    raw_description = Path(file_path).read_text()
    validated_model = DescriptionSpec.model_validate_json(raw_description)

    logger.debug(f"Loaded and validated description JSON: {file_path}")

    return validated_model


def read_description_spreadsheet(
    sheet_path: Path, sheet_info: dict[str, Any], sheet_type: str
) -> dict[str, pd.DataFrame]:
    """
    Read and parse specific sheets from a metadata spreadsheet.

    Iterates through the provided configuration to load Excel/ODS sheets
    into pandas DataFrames. Each entry in `sheet_info` is passed as
    keyword arguments to the underlying pandas reader.

    Parameters
    ----------
    sheet_path : Path
        The path to the spreadsheet file (e.g., .xlsx, .ods).
    sheet_info : dict[str, Any]
        A mapping where keys are labels (e.g., 'datasheet', 'codebook')
        and values are dictionaries of parameters for `pd.read_excel`.
    sheet_type : str
        A descriptive label for the data being loaded (e.g., 'participant'),
        used primarily for logging.

    Returns
    -------
    dict[str, pd.DataFrame]
        A dictionary where keys match `sheet_info` and values are the
        corresponding loaded pandas DataFrames.
    """
    sheet_dict = {key: pd.read_excel(sheet_path, **val) for key, val in sheet_info.items()}

    logger.debug(f"Loaded {sheet_type} info from {sheet_path}")

    return sheet_dict


def read_eeg_recording(recording_path: Path) -> BaseRaw:
    """
    Read a raw EEG recording and normalize its measurement date.

    Loads the EEG data from the specified path and updates the internal
    measurement date to the current date in UTC format.

    Parameters
    ----------
    recording_path : Path
        The file path to the raw EEG recording.

    Returns
    -------
    BaseRaw
        The loaded MNE Raw object with the updated measurement date.

    Notes
    -----
    This function utilizes the `read_raw` helper, which automatically
    detects the appropriate MNE reader based on file extension.
    """
    eeg_data = read_raw(recording_path)
    eeg_data.set_meas_date(get_utc_today())

    return eeg_data


def read_bids_tsv(tsv_path: Path) -> pd.DataFrame:
    """
    Read a BIDS-compliant TSV file into a pandas DataFrame.

    Parses a tab-separated file located at the provided BIDSPath,
    automatically setting the first column as the index.

    Parameters
    ----------
    tsv_path : Path
        The Path object pointing to the target .tsv file.

    Returns
    -------
    pd.DataFrame
        The loaded data contained in the TSV file.

    Notes
    -----
    This function assumes a standard BIDS structure where files are
    tab-separated and contain a leading index/header column.
    """
    return pd.read_csv(tsv_path, sep="\t", index_col=0)


def write_enriched_sidecar(bids_path: BIDSPath, updates: dict[str, Any]):
    """
    Update the JSON sidecar file associated with a BIDS EEG recording.

    Constructs the correct path for the EEG sidecar file by modifying the
    extension and suffix of the provided BIDSPath, then applies
    specified metadata updates.

    Parameters
    ----------
    bids_path : BIDSPath
        The BIDSPath object corresponding to the recording.
    updates : dict[str, Any]
        A dictionary of key-value pairs to be added or updated in the
        target JSON sidecar.

    Returns
    -------
    None
        Modifies the sidecar JSON file on disk.

    Notes
    -----
    This function internally calls `update_sidecar_json` and assumes a
    standard BIDS suffix of 'eeg' and extension '.json'.
    """
    sidecar_path = bids_path.copy().update(extension=".json", suffix="eeg", datatype="eeg")

    update_sidecar_json(sidecar_path, updates)


def write_bids_tsv(tsv_path: Path, tsv_df: pd.DataFrame):
    """
    Write a pandas DataFrame to a BIDS-compliant TSV file.

    Exports the provided data to disk at the location specified by the
    BIDSPath, ensuring the use of tab separators.

    Parameters
    ----------
    tsv_path : Path
        The Path object defining the destination for the .tsv file.
    tsv_df : pd.DataFrame
        The DataFrame containing the data to be written.

    Returns
    -------
    None
        Writes the TSV file to disk.
    """
    tsv_df.to_csv(tsv_path, sep="\t")


def write_phenotype_data(phenotype_data: dict[str, pd.DataFrame], root_path: Path, missing_ids: list[str]):
    """
    Write filtered phenotype data and associated codebooks to the BIDS dataset.

    Creates a 'phenotype' directory in the root path. Before exporting, it
    prunes the phenotype dataset to exclude any participants identified in
    'missing_ids', ensuring the metadata remains synchronized with the
    available EEG recordings.

    Parameters
    ----------
    phenotype_data : dict[str, pd.DataFrame]
        A dictionary containing the phenotype information. Must include
        'dataset' (the actual values) and 'codebook' (metadata) as DataFrames.
    root_path : Path
        The root directory of the BIDS dataset where the '/phenotype'
        folder will be created.
    missing_ids : list[str]
        A list of subject identifiers to be filtered out of the phenotype
        dataset before writing to disk.

    Returns
    -------
    None
        Writes 'phenotype.tsv' and 'phenotype.json' to the filesystem.

    Notes
    -----
    The codebook is exported using a JSON 'index' orientation to map
    variable names to their respective descriptions and metadata,
    aligning with BIDS recommendations for sidecar files.
    """
    phenotype_path = root_path / "phenotype"

    phenotype_path.mkdir(parents=True, exist_ok=True)

    phenotype_data["dataset"] = filter_dataframe_by_valid_ids(phenotype_data["dataset"], missing_ids)
    phenotype_data["dataset"].to_csv(phenotype_path / "phenotype.tsv", sep="\t")
    phenotype_data["codebook"].to_json(phenotype_path / "phenotype.json", orient="index")

    logger.debug(f"Phenotype data written to {phenotype_path}")


def check_task_exists(subject_dir: Path, task: str) -> bool:
    """
    Check for the existence of specific task files within a subject directory.

    Scans the subject's BIDS folder to identify if any files associated
    with the given task label have already been generated.

    Parameters
    ----------
    subject_dir : Path
        The BIDS subject-level directory (e.g., 'sub-001/') to be searched.
    task : str
        The BIDS task label to search for (e.g., 'rest', 'faceprocessing').

    Returns
    -------
    bool
        True if the directory exists and contains at least one file
        matching the task pattern; False otherwise.
    """
    if not subject_dir.exists():
        return False

    return any(subject_dir.rglob(f"*task-{task}*"))


def rollback_recording_files(subject_dir: Path, recording: RecordingMetadata):
    """
    Remove partial or corrupted files following an export failure.

    Provides an automated cleanup mechanism to prevent data pollution. If
    a specific condition is provided, it targets only files associated
    with that task; otherwise, it removes the entire subject directory.

    Parameters
    ----------
    subject_dir : Path
        The BIDS subject-level directory (e.g., 'sub-001/') where the
        failed export occurred.
    recording : RecordingMetadata
        Metadata for the failed recording, used to identify specific
        task labels and provide context for logging.

    Returns
    -------
    None
        Deletes files or directories from the filesystem and logs the
        outcome.
    """
    if not subject_dir.exists():
        return

    try:
        if recording.condition:
            failed_files = subject_dir.rglob(f"*task-{recording.task}*")
            [file_path.unlink() for file_path in failed_files if file_path.is_file()]
            logger.info(f"{recording.info_str} - Cleaned up partial task files")
        else:
            shutil.rmtree(subject_dir)
            logger.info(f"{recording.info_str} - Cleaned up incomplete BIDS folder")
    except Exception as cleanup_error:
        logger.error(f"{recording.info_str} - Clean up failed: {cleanup_error}")


def cleanup_participants_tsv(expected_ids: list[str], out_path: Path) -> list[str]:
    """
    Synchronize the participants TSV with the physical BIDS directory.

    Identifies discrepancies between the participant folders present on disk
    and the IDs expected by the protocol. If a discrepancy is found, it
    removes the missing IDs from 'participants.tsv' to ensure metadata
    integrity.

    Parameters
    ----------
    expected_ids : list[str]
        A list of BIDS-compliant subject strings (e.g., ['sub-001', 'sub-002'])
        that were originally planned for processing.
    out_path : Path
        The root directory of the BIDS dataset containing the subject folders
        and the 'participants.tsv' file.

    Returns
    -------
    list[str]
        A list of the missing or removed identifiers identified during the
        cleanup process.
    """
    present_ids = [path.name for path in out_path.iterdir() if path.is_dir() and path.name.startswith("sub")]

    if missing_ids := list(set(expected_ids).symmetric_difference(present_ids)):
        tsv_path = out_path / "participants.tsv"

        participant_tsv = read_bids_tsv(tsv_path)

        cleaned_tsv = filter_dataframe_by_valid_ids(participant_tsv, missing_ids)

        write_bids_tsv(tsv_path, cleaned_tsv)

    return missing_ids
