import logging

from pathlib import Path

from rs_bidsify import io
from rs_bidsify.config_loader import PARTICIPANT_INFO as part_info, PHENOTYPE_INFO as phen_info
from rs_bidsify.validation.description import DescriptionSpec

logger = logging.getLogger(__name__)

def find_file(path: Path, ext: str):
    found_path = list(path.glob(f"*.{ext}"))

    if len(found_path) != 1:
        raise ValueError(
            f"Expected single {ext} file in {path}, instead found {len(found_path)}"
        )

    return found_path[0]


def find_description_spec(raw_path: Path, extension: str = "json") -> DescriptionSpec:
    """Find and load the dataset metadata specification"""
    json_path = find_file(raw_path, extension)
    return io.read_description_json(json_path)


def find_dataset_spreadsheets(
    raw_path: Path, sheet_info: dict[str, dict], extension: str = "ods"
) -> tuple[dict, dict | None]:
    """Find and load the dataset"""

    sheet_path = find_file(raw_path, extension)

    participant_data = io.read_description_spreadsheet(
        sheet_path, sheet_info["participant"], "participant"
    )
    try:
        phenotype_data = io.read_description_spreadsheet(sheet_path, sheet_info["phenotype"], "phenotype")
    except Exception:
        # When the data is not available
        logger.error(f"Phenotype data could not be loaded from {sheet_path}")
        phenotype_data = None

    return participant_data, phenotype_data
