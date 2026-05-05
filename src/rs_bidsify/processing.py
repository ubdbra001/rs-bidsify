from pathlib import Path

from rs_bidsify import data_io
from rs_bidsify.config import PARTICIPANT_INFO as part_info, PHENOTYPE_INFO as phen_info
from rs_bidsify.validation.description import DatasetDescription
from rs_bidsify.utils import find_file

def generate_dataset_description(root_path: Path):

    json_path = find_file(root_path, "json")
    sheet_path = find_file(root_path, "ods")

    dataset_spec = data_io.read_description_json(json_path)
    participant_data = data_io.read_description_spreadsheet(sheet_path, part_info)
    phenotype_data = data_io.read_description_spreadsheet(sheet_path, phen_info)

    return DatasetDescription(spec=dataset_spec, participants=participant_data, phenotype=phenotype_data)

