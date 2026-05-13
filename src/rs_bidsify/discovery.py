from pathlib import Path

from rs_bidsify import io
from rs_bidsify.config import PARTICIPANT_INFO as part_info, PHENOTYPE_INFO as phen_info
from rs_bidsify.validation.description import DescriptionSpec


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
    raw_path: Path, extension: str = "ods"
) -> tuple[dict, dict]:
    """Find and load the dataset"""

    sheet_path = find_file(raw_path, extension)

    participant_data = io.read_description_spreadsheet(
        sheet_path, part_info, "participant"
    )
    phenotype_data = io.read_description_spreadsheet(sheet_path, phen_info, "phenotype")

    return participant_data, phenotype_data
