from enum import IntEnum, Enum
from typing import Literal, Any
from pandas import DataFrame
from dataclasses import dataclass, field

from pydantic import BaseModel, PositiveInt, Field, model_validator, FilePath


class MNEChanTypes(str, Enum):
    """Enum listing all of the different channel types available in MNE"""

    # This list could probably be reduced to channels specifically relevant to EEG
    BIO = "bio"
    CHPI = "chpi"
    DBS = "dbs"
    DIPOLE = "dipole"
    ECG = "ecg"
    ECOG = "ecog"
    EMG = "emg"
    EOG = "eog"
    EXCI = "exci"
    EYETRACK = "eyetrack"
    FNIRS = "fnirs"
    GOF = "gof"
    GSR = "gsr"
    IAS = "ias"
    MISC = "misc"
    MEG = "meg"
    REF_MEG = "ref_meg"
    RESP = "resp"
    SEEG = "seeg"
    STIM = "stim"
    SYST = "syst"
    TEMPERATURE = "temperature"


class BIDSChanTypes(str, Enum):
    """Enum listing all of the different channel types available in BIDS"""

    # This list could probably be reduced to channels specifically relevant to EEG
    ACCEL = "ACCEL"
    ADC = "ADC"
    ANGACCEL = "ANGACCEL"
    AUDIO = "AUDIO"
    DAC = "DAC"
    DBS = "DBS"
    ECG = "ECG"
    ECOG = "ECOG"
    EEG = "EEG"
    EMG = "EMG"
    EOG = "EOG"
    EYEGAZE = "EYEGAZE"
    FITERR = "FITERR"
    GSR = "GSR"
    GYRO = "GYRO"
    HEOG = "HEOG"
    HLU = "HLU"
    JNTANG = "JNTANG"
    LATENCY = "LATENCY"
    MAGN = "MAGN"
    MEGGRADAXIAL = "MEGGRADAXIAL"
    MEGGRADPLANAR = "MEGGRADPLANAR"
    MEGMAG = "MEGMAG"
    MEGOTHER = "MEGOTHER"
    MEGREFGRADAXIAL = "MEGREFGRADAXIAL"
    MEGREFGRADPLANAR = "MEGREFGRADPLANAR"
    MEGREFMAG = "MEGREFMAG"
    MISC = "MISC"
    NIRSCWAMPLITUDE = "NIRSCWAMPLITUDE"
    NIRSCWFLUORESCENSEAMPLITUDE = "NIRSCWFLUORESCENSEAMPLITUDE"
    NIRSCWHBO = "NIRSCWHBO"
    NIRSCWHBR = "NIRSCWHBR"
    NIRSCWMUA = "NIRSCWMUA"
    NIRSCWOPTICALDENSITY = "NIRSCWOPTICALDENSITY"
    ORNT = "ORNT"
    OTHER = "OTHER"
    PD = "PD"
    POS = "POS"
    PPG = "PPG"
    PUPIL = "PUPIL"
    REF = "REF"
    RESP = "RESP"
    SEEG = "SEEG"
    SYSCLOCK = "SYSCLOCK"
    TEMP = "TEMP"
    TRIG = "TRIG"
    VEL = "VEL"
    VEOG = "VEOG"


class LineFreqOptions(IntEnum):
    """Worldwide powerline frequency options"""

    FIFTY = 50
    SIXTY = 60


class EthicsApprovalOptions(str, Enum):
    """Options for ethical approval"""

    APPROVED = "Approved"
    NOT_REQUIRED = "Not Required"


class FilterTypeOptions(str, Enum):
    """Options for different online filtering sources"""

    HARDWARE = "Hardware"
    SOFTWARE = "Software"


class DatasetMetadata(BaseModel):
    """Schema defining structure for the dataset_metadata section of the
    machine readable dataset description"""

    number_sessions: PositiveInt
    population: str
    dataset_name: str
    authors: list[str]
    funding: str | list[str] | None = None
    ethics_approval: EthicsApprovalOptions
    license: str
    references_links: str | list[str]
    institution_name: str
    institution_dept: str


class Montage(BaseModel):
    mne_name: str | None = (
        None  # It might be best to limit this to standard montages in MNE (https://mne.tools/stable/auto_tutorials/intro/40_sensor_locations.html)
    )
    path: FilePath | None = None

    @model_validator(mode="after")
    def check_path_for_other_montages(self) -> "Montage":
        if self.mne_name is None and self.path is None:
            raise ValueError("Field 'path' is required when 'mne_name' is not provided")
        return self


class EEGChanSpec(BaseModel):
    """Schema defining structure for the eeg_channels sub-section of the
    machine readable dataset description"""

    number: PositiveInt
    montage: Montage
    ground: str
    reference: str


class AuxChanSpec(BaseModel):
    """Schema defining structure for the aux_channels sub-section of the
    machine readable dataset description"""

    mne_type: MNEChanTypes
    bids_type: BIDSChanTypes
    description: str | None = None  # Optional
    units: str | None = None  # Optional
    location: (
        str | dict[str, str]
    )  # Leaving the location dict relatively free-form here


class AcceptableImpedance(BaseModel):
    """Schema defining structure for the acceptable_impedance sub-section of the
    machine readable dataset description"""

    value: int
    units: str


class LightingConditions(BaseModel):
    """Schema defining structure for the lighting_conditions sub-section of the
    machine readable dataset description"""

    description: str
    measurement: str


class FilterSpec(BaseModel):
    """Schema defining structure for the filters sub-section of the
    machine readable dataset description"""

    name: str
    type: FilterTypeOptions
    info: dict[
        str, Any
    ]  # This dict will be copied directly to the eeg sidecar, so should contain that info directly


class AcquisitionSpecs(BaseModel):
    """Schema defining structure for the recording_info section of the
    machine readable dataset description"""

    software: str
    acquisition_freq: PositiveInt
    file_format: str
    amplifier_model: str
    eeg_channels: EEGChanSpec
    aux_channels: dict[str, AuxChanSpec]
    power_line_freq: LineFreqOptions
    filters: list[FilterSpec]
    acceptable_impedance: AcceptableImpedance
    electrode_type: str
    conductive_medium: str
    faraday_cage: bool
    sound_proof: bool
    lighting_conditions: LightingConditions | None = None


class RestingStateTask(BaseModel):
    """Base schema defining structure for different resting state conditions"""

    stimulus_description: str | None = None
    duration_secs: PositiveInt


class EyesOpenTask(RestingStateTask):
    """Specific schema defining the structure for the eyes-open RS condition"""

    stimulus_description: str  # Description is not optional for eyes-open


class EyesClosedTask(RestingStateTask):
    """Specific schema defining the structure for the eyes-closed RS condition"""

    stimulus_description: Literal[None] = Field(
        default=None, exclude=True
    )  # No Description for eyes-closed


class CustomRestingTask(RestingStateTask):
    """Specific schema defining the structure for any other potential RS conditions"""

    condition_name: str
    stimulus_description: str


class RestingStateProtocol(BaseModel):
    """Schema defining the structure for all the RS conditions recorded during a dataset"""

    instructions: str
    eyes_open: EyesOpenTask | Literal[False]
    eyes_closed: EyesClosedTask | Literal[False]
    other_conditions: list[CustomRestingTask] | None = None
    events: dict[str, str]  # Should be defined as "event code": "event description"


class DatasetSpec(BaseModel):
    """Overarching schema for the dataset description"""

    metadata: DatasetMetadata
    conditions: list[str] | None = Field(default=None, min_length=1)
    sessions: list[str] | None = Field(default=None, min_length=1)
    acquisition_spec: AcquisitionSpecs
    resting_state: RestingStateProtocol

@dataclass
class DatasetDescription:

    spec: DatasetSpec
    participants: dict[str, DataFrame] = field(default_factory=dict)
    phenotype: dict[str, DataFrame] = field(default_factory=dict)

    @property
    def crawler_info(self):
        return {
            "expected_participants": self.participants["dataset"].index.to_list(),
            "expected_conditions": self.spec.conditions,
            "expected_sessions": self.spec.sessions,
            "extension": self.spec.acquisition_spec.file_format
        }


