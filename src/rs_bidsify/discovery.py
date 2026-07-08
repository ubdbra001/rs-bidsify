import logging
from pathlib import Path

from rs_bidsify import io
from rs_bidsify.validation.description import DescriptionSpec

logger = logging.getLogger(__name__)


def find_file(path: Path, ext: str, keyword: str = "") -> Path:
    """
    Locate a single file with a specific extension within a directory.

    This function searches the specified directory for files matching the
    provided extension, and keyword. It enforces a strict requirement that exactly one
    matching file must exist.

    Parameters
    ----------
    path : Path
        The directory path to search within.
    ext : str
        The file extension to look for (e.g., 'json', 'nii.gz').
        Do not include the leading dot.
    keyword : str, optional
        An additional label for identifying the file to find.
        Default = ""

    Returns
    -------
    Path
        The path to the unique file found.

    Raises
    ------
    ValueError
        If no files or multiple files with the given keyword and extension
        are found in the directory.
    """
    pattern = f"*{keyword}.{ext}"
    found_path = list(path.glob(pattern))

    if len(found_path) != 1:
        raise ValueError(f"Expected single file matching {pattern} in {path}, instead found {len(found_path)}")

    return found_path[0]


def find_description_spec(raw_path: Path, extension: str = "toml") -> DescriptionSpec:
    """
    Locate and load the dataset description metadata file.

    Utilises file discovery to find a unique metadata file with the
    specified extension and parses its content into a DescriptionSpec object.

    Parameters
    ----------
    raw_path : Path
        The directory path to search for the description file.
    extension : str, optional
        The file extension to search for, by default "toml".

    Returns
    -------
    DescriptionSpec
        The parsed metadata specification object.

    Notes
    -----
    This function relies on `find_file`, which will raise a ValueError if
    zero or multiple files matching the extension are found.
    """
    file_path = find_file(raw_path, ext=extension, keyword="metadata")
    return io.read_description_file(file_path)


def find_dataset_spreadsheets(
    raw_path: Path, sheet_info: dict[str, dict], extension: str = "ods"
) -> tuple[dict, dict | None]:
    """
    Locate and parse participant and phenotype data from a spreadsheet.

    Searches for a unique spreadsheet file and attempts to extract two
    distinct datasets based on the provided sheet information. If the
    phenotype data fails to load, it is returned as None while
    logging an error.

    Parameters
    ----------
    raw_path : Path
        The directory path to search for the spreadsheet file.
    sheet_info : dict[str, dict]
        A dictionary containing configuration details for the sheets
        to be read (e.g., sheet names or column mappings).
    extension : str, optional
        The file extension to search for, by default "ods".

    Returns
    -------
    participant_data : dict
        The parsed data for participants.
    phenotype_data : dict or None
        The parsed phenotype data, or None if the data could not be loaded.

    Notes
    -----
    This function utilises `find_file`, which raises a ValueError if
    the spreadsheet is not uniquely identified.
    """
    sheet_path = find_file(raw_path, extension)

    participant_data = io.read_description_spreadsheet(sheet_path, sheet_info["participant"], "participant")

    phenotype_data = None

    if sheet_info.get("phenotype"):
        try:
            phenotype_data = io.read_description_spreadsheet(sheet_path, sheet_info["phenotype"], "phenotype")
        except Exception:
            # When the data is not available
            logger.error(f"Phenotype data could not be loaded from {sheet_path}")

    return participant_data, phenotype_data


def find_missing_subjects(expected_ids: list[str], out_path: Path) -> list[str]:
    """
    Identify expected subjects that are missing from the BIDS output directory.

    Scans the filesystem to determine which participants from the initial
    protocol were not successfully exported, allowing for targeted
    metadata cleanup.

    Parameters
    ----------
    expected_ids : list[str]
        A list of BIDS-compliant subject strings (e.g., ['sub-01', 'sub-02'])
        originally slated for processing.
    out_path : Path
        The root directory of the BIDS dataset to be scanned for subject folders.

    Returns
    -------
    list[str]
        A list of subject identifiers present in 'expected_ids' but missing
        from the physical directory.
    """
    present_ids = [path.name for path in out_path.iterdir() if path.is_dir() and path.name.startswith("sub")]

    return list(set(expected_ids) - set(present_ids))
