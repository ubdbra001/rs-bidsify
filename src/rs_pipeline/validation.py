from enum import IntEnum, Enum
from pydantic import BaseModel, PositiveInt, Field
from typing import Literal, Any


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


class DatasetInfo(BaseModel):
    """Schema defining structure for the dataset_info section of the
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


class EEGChannelInfo(BaseModel):
    """Schema defining structure for the eeg_channels sub-section of the
    machine readable dataset description"""

    number: PositiveInt
    montage: str  # This could be the different options available in MNE, but for now it is left to be as flexible as possible
    ground: str
    reference: str


class OtherChannelInfo(BaseModel):
    """Schema defining structure for the other_channels sub-section of the
    machine readable dataset description"""

    mne_type: MNEChanTypes
    bids_type: BIDSChanTypes
    description: str | None = None  # Optional
    units: str | None = None  # Optional
    location: (
        str | dict[str, str]
    )  # Leaving the location dict relatively free-form here


class ImpedanceInfo(BaseModel):
    """Schema defining structure for the acceptable_impedance sub-section of the
    machine readable dataset description"""

    value: int
    units: str


class LightingConditions(BaseModel):
    """Schema defining structure for the lighting_conditions sub-section of the
    machine readable dataset description"""

    description: str
    measurement: str


class FilterInfo(BaseModel):
    """Schema defining structure for the filters sub-section of the
    machine readable dataset description"""

    name: str
    type: FilterTypeOptions
    info: dict[
        str, Any
    ]  # This dict will be copied directly to the eeg sidecar, so should contain that info directly


class RecordingInfo(BaseModel):
    """Schema defining structure for the recording_info section of the
    machine readable dataset description"""

    software: str
    acquisition_freq: PositiveInt
    file_format: str
    amplifier_model: str
    eeg_channels: EEGChannelInfo
    other_channels: dict[str, OtherChannelInfo]
    power_line_freq: LineFreqOptions
    filters: list[FilterInfo]
    acceptable_impedance: ImpedanceInfo
    electrode_type: str
    conductive_medium: str
    faraday_cage: bool
    sound_proof: bool
    lighting_conditions: LightingConditions | None = None


class RestingStateCondition(BaseModel):
    """Base schema defining structure for different resting state conditions"""

    stimulus_description: str | None = None
    duration_secs: PositiveInt


class EyesOpenCondition(RestingStateCondition):
    """Specific schema defining the structure for the eyes-open RS condition"""

    stimulus_description: str  # Description is not optional for eyes-open


class EyesClosedCondition(RestingStateCondition):
    """Specific schema defining the structure for the eyes-closed RS condition"""

    stimulus_description: Literal[None] = Field(
        default=None, exclude=True
    )  # No Description for eyes-closed


class OtherRSCondition(RestingStateCondition):
    """Specific schema defining the structure for any other potential RS conditions"""

    condition_name: str
    stimulus_description: str


class RestingStateInfo(BaseModel):
    """Schema defining the structure for all the RS conditions recorded during a dataset"""

    instructions: str
    eyes_open: EyesOpenCondition | Literal[False]
    eyes_closed: EyesClosedCondition | Literal[False]
    other_conditions: list[OtherRSCondition] | None = None
    events: dict[str, str]  # Should be defined as "event code": "event description"


class FullDatasetInfo(BaseModel):
    """Overarching schema for the dataset description"""

    dataset_info: DatasetInfo
    recording_info: RecordingInfo
    resting_state_info: RestingStateInfo
