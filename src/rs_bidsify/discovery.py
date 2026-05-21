import logging

from pathlib import Path

from rs_bidsify import io
from rs_bidsify.validation.description import DescriptionSpec

logger = logging.getLogger(__name__)


def find_file(path: Path, ext: str):
    """
    Locate a single file with a specific extension within a directory.

    This function searches the specified directory for files matching the 
    provided extension. It enforces a strict requirement that exactly one 
    matching file must exist.

    Parameters
    ----------
    path : Path
        The directory path to search within.
    ext : str
        The file extension to look for (e.g., 'json', 'nii.gz'). 
        Do not include the leading dot.

    Returns
    -------
    Path
        The path to the unique file found.

    Raises
    ------
    ValueError
        If no files or multiple files with the given extension are found 
        in the directory.
    """
    found_path = list(path.glob(f"*.{ext}"))

    if len(found_path) != 1:
        raise ValueError(
            f"Expected single {ext} file in {path}, instead found {len(found_path)}"
        )

    return found_path[0]


def find_description_spec(raw_path: Path, extension: str = "json") -> DescriptionSpec:
    """
    Locate and load the dataset description metadata file.

    Utilizes file discovery to find a unique metadata file with the 
    specified extension and parses its content into a DescriptionSpec object.

    Parameters
    ----------
    raw_path : Path
        The directory path to search for the description file.
    extension : str, optional
        The file extension to search for, by default "json".

    Returns
    -------
    DescriptionSpec
        The parsed metadata specification object.

    Notes
    -----
    This function relies on `find_file`, which will raise a ValueError if 
    zero or multiple files matching the extension are found.
    """
    json_path = find_file(raw_path, extension)
    return io.read_description_json(json_path)


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
    This function utilizes `find_file`, which raises a ValueError if 
    the spreadsheet is not uniquely identified.
    """
    sheet_path = find_file(raw_path, extension)

    participant_data = io.read_description_spreadsheet(
        sheet_path, sheet_info["participant"], "participant"
    )
    try:
        phenotype_data = io.read_description_spreadsheet(
            sheet_path, sheet_info["phenotype"], "phenotype"
        )
    except Exception:
        # When the data is not available
        logger.error(f"Phenotype data could not be loaded from {sheet_path}")
        phenotype_data = None

    return participant_data, phenotype_data
