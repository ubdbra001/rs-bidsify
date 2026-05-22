import logging
from pathlib import Path
from typing import Any
from rs_bidsify.utils import get_utc_today
from rs_bidsify.validation.description import DescriptionSpec
from rs_bidsify.validation.dataset import RecordingMetadata


import pandas as pd
from mne.io import read_raw, BaseRaw

from mne_bids import BIDSPath, write_raw_bids, update_sidecar_json

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

    logger.info(f"Loaded and validated description JSON: {file_path}")

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
    sheet_dict = {
        key: pd.read_excel(sheet_path, **val) for key, val in sheet_info.items()
    }

    logger.info(f"Loaded {sheet_type} info from {sheet_path}")

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


def read_bids_tsv(tsv_path: BIDSPath):
    """
    Read a BIDS-compliant TSV file into a pandas DataFrame.

    Parses a tab-separated file located at the provided BIDSPath,
    automatically setting the first column as the index.

    Parameters
    ----------
    tsv_path : BIDSPath
        The BIDSPath object pointing to the target .tsv file.

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


def write_bids(
    bids_root: Path,
    eeg_data: BaseRaw,
    recording: RecordingMetadata,
    out_format: str = "EDF",
) -> BIDSPath:
    """
    Export an EEG recording to the BIDS directory structure.

    Constructs a BIDS-compliant path using subject and condition metadata
    and writes the raw EEG data to disk. By default, existing files at
    the destination are overwritten.

    Parameters
    ----------
    bids_root : Path
        The root directory of the BIDS dataset.
    eeg_data : BaseRaw
        The MNE Raw object containing the EEG data and info.
    recording : RecordingMetadata
        A metadata object containing at least `subject` and `condition`
        attributes to define the BIDS entity.
    out_format : str, optional
        The output file format for the EEG data, by default "EDF".

    Returns
    -------
    BIDSPath
        The resulting BIDSPath object indicating where the data was written.

    Notes
    -----
    This function calls `write_raw_bids` with `overwrite=True` and
    `allow_preload=True` enabled.
    """
    bids_path = BIDSPath(
        subject=recording.subject,
        task=recording.condition,
        root=bids_root,
    )

    return write_raw_bids(
        eeg_data, bids_path, overwrite=True, allow_preload=True, format=out_format
    )


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
    sidecar_path = bids_path.copy().update(
        extension=".json", suffix="eeg", datatype="eeg"
    )

    update_sidecar_json(sidecar_path, updates)


def write_bids_tsv(tsv_path: BIDSPath, tsv_df: pd.DataFrame):
    """
    Write a pandas DataFrame to a BIDS-compliant TSV file.

    Exports the provided data to disk at the location specified by the
    BIDSPath, ensuring the use of tab separators.

    Parameters
    ----------
    tsv_path : BIDSPath
        The BIDSPath object defining the destination for the .tsv file.
    tsv_df : pd.DataFrame
        The DataFrame containing the data to be written.

    Returns
    -------
    None
        Writes the TSV file to disk.
    """
    tsv_df.to_csv(tsv_path, sep="\t")


def write_phenotype_data(phenotype_data: dict[str, pd.DataFrame], root_path: Path):
    """
    Write phenotype data and its associated codebook to the dataset root.

    Creates a 'phenotype' directory within the root path and exports the
    dataset as a TSV file and the codebook as a JSON file.

    Parameters
    ----------
    phenotype_data : dict[str, pd.DataFrame]
        A dictionary containing the phenotype information. Must include
        'dataset' (DataFrame) and 'codebook' (DataFrame) keys.
    root_path : Path
        The root directory of the BIDS dataset where the phenotype
        folder will be created.

    Returns
    -------
    None
        Writes files to disk and logs the output location.

    Notes
    -----
    The codebook is exported using a JSON 'index' orientation to map
    variable names to their respective descriptions and metadata.
    """
    phenotype_path = root_path / "phenotype"

    phenotype_path.mkdir(parents=True, exist_ok=True)

    phenotype_data["dataset"].to_csv(phenotype_path / "phenotype.tsv", sep="\t")
    phenotype_data["codebook"].to_json(
        phenotype_path / "phenotype.json", orient="index"
    )

    logger.info(f"Phenotype data written to {phenotype_path}")
