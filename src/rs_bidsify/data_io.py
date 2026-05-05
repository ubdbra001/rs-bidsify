import logging
from pathlib import Path
from typing import Any
from rs_bidsify.utils import get_utc_today
from rs_bidsify.validation.description import DatasetSpec
from rs_bidsify.validation.dataset import RecordingMetadata


import pandas as pd
from mne.io import read_raw, BaseRaw

from mne_bids import BIDSPath, write_raw_bids, update_sidecar_json

logger = logging.getLogger(__name__)

def read_description_json(file_path: Path) -> DatasetSpec:
    """Reads and validates the description json file.

    Parameters
    ----------
    file_path : file_path_type
        Path to description json file

    Returns
    -------
    DatasetSpec
        Validated JSON file in a Pydantic Model
    """
    raw_description = Path(file_path).read_text()
    validated_model = DatasetSpec.model_validate_json(raw_description)

    logger.info(f"Loaded and validated description JSON: {file_path}")

    return validated_model

def read_description_spreadsheet(sheet_path: Path, sheet_info: dict[str, Any], sheet_type: str) -> dict[str, pd.DataFrame]:
    """Read sheets from the description spreadsheet

    Parameters
    ----------
    sheet_path : Path
        Path to metadata spreadsheet
    sheet_info : dict[str, Any]
        Dictionary providing information about how to extract the data from the sheet (e.g. sheet name, index column)

    Returns
    -------
    dict[str, pd.DataFrame]
        Dictionary containing the loaded sheet(s), will typically consist of a datasheet and a codebook for the datasheet
    """    
    
    sheet_dict = {key: pd.read_excel(sheet_path, **val) for key, val in sheet_info.items()}
    
    logger.info(f"Loaded {sheet_type} info from {sheet_path}")

    return sheet_dict


def read_eeg_recording(recording_path: Path) -> BaseRaw:
    """Read in a raw EEG recording"""

    eeg_data = read_raw(recording_path)
    eeg_data.set_meas_date(get_utc_today())

    return eeg_data

def write_bids(bids_root: Path, eeg_data: BaseRaw, recording: RecordingMetadata) -> BIDSPath:
    """Write EEG recording to BIDS"""

    bids_path = BIDSPath(
        subject=recording.subject,
        task=recording.condition,
        session=recording.session,
        root=bids_root
    )
    
    return write_raw_bids(eeg_data, bids_path, overwrite=True, allow_preload=True, format="EDF")

def write_enriched_sidecar(bids_path: BIDSPath, updates: dict[str, Any]):
    """Write post-creation updates to sidecar"""

    sidecar_path = bids_path.copy().update(
        extension='.json', suffix="eeg", datatype='eeg'
    )

    update_sidecar_json(sidecar_path, updates)

