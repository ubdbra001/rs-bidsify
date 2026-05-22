import logging
from enum import Enum, IntEnum
from functools import cached_property
from typing import Any, Literal, Self

from mne.channels import (
    DigMontage,
    get_builtin_montages,
    make_standard_montage,
    read_custom_montage,
)
from pydantic import (
    BaseModel,
    Field,
    FilePath,
    PositiveInt,
    field_validator,
    model_validator,
)

from rs_bidsify.utils import apply_dynamic_value
from rs_bidsify.validation.subject import SubjectMetadata

logger = logging.getLogger(__name__)


class MNEChanTypes(str, Enum):
    """
    Standard channel types recognized by MNE-Python.

    Lower-case strings corresponding to the types allowed in
    mne.io.Raw.set_channel_types.
    """

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
    """
    Channel types defined by the BIDS specification.

    Upper-case strings used in the 'type' column of BIDS channels.tsv files.
    """

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
    """Supported powerline frequencies for MNE and BIDS metadata."""

    FIFTY = 50
    SIXTY = 60


class EthicsApprovalOptions(str, Enum):
    """Status options for institutional ethical approval."""

    APPROVED = "Approved"
    NOT_REQUIRED = "Not Required"


class FilterTypeOptions(str, Enum):
    """Options for different online filtering sources."""

    HARDWARE = "Hardware"
    SOFTWARE = "Software"


class DatasetMetadata(BaseModel):
    """
    Schema for top-level BIDS dataset metadata.

    Defines the global information required for the dataset description,
    including institutional details, funding, and ethical approval status.
    """

    population: str
    dataset_name: str
    authors: list[str]
    funding: str | list[str] | None = None
    ethics_approval: EthicsApprovalOptions
    license: str
    references_links: str | list[str]
    institution_name: str
    institution_dept: str

    def create_dict(self) -> dict:
        """
        Generate a dictionary formatted for BIDS dataset_description.json.

        Maps internal model fields to official BIDS-compliant keys.
        """
        return {
            "name": self.dataset_name,
            "data_license": self.license,
            "authors": self.authors,
            "references_and_links": self.references_links,
            "funding": self.funding,
        }


class Montage(BaseModel):
    """
    Configuration for sensor locations and coordinate frames.

    Ensures that a valid electrode montage is provided, either by
    referencing a built-in MNE montage name or providing a path to
    a custom sensor file.

    Attributes
    ----------
    mne_name : str or None
        Name of a built-in MNE montage (e.g., 'standard_1020'). If provided,
        must be a recognized string in MNE's built-in montages.
    path : FilePath or None
        Valid path to a custom sensor location file on the local system.
    """

    mne_name: str | None = None
    path: FilePath | None = None

    @field_validator("mne_name")
    @classmethod
    def validate_mne_name(cls, v: str | None) -> str | None:
        """
        Validate that the provided montage name is built into MNE.

        Parameters
        ----------
        v : str or None
            The standard montage name to check.

        Returns
        -------
        str or None
            The validated montage name.

        Raises
        ------
        ValueError
            If the provided name is not found in MNE's built-in montages.
        """
        if v is not None:
            valid_montages = get_builtin_montages()
            if v not in valid_montages:
                raise ValueError(f"'{v}' is not a valid built-in MNE montage. ")
        return v

    @model_validator(mode="after")
    def check_input_exclusivity(self) -> Self:
        """
        Ensure exactly one source for the montage is provided.

        Validates that either an MNE name or a custom file path is defined,
        but strictly prevents providing both or neither.

        Returns
        -------
        Self
            The validated model instance.

        Raises
        ------
        ValueError
            If both `mne_name` and `path` are provided, or if neither are provided.
        """
        if self.mne_name is None and self.path is None:
            raise ValueError("Need to provide either 'mne_name' or 'path' fields")

        if self.mne_name is not None and self.path is not None:
            raise ValueError(
                "Only one of either 'mne_name' or 'path' fields need to be provided"
            )

        return self

    @cached_property
    def montage(self) -> DigMontage:
        """
        Lazily generate and return the MNE DigMontage object.

        Uses cached_property to ensure the file or standard library is
        only read once upon the first access, improving performance.

        Returns
        -------
        DigMontage
            The constructed or loaded MNE montage object.

        Raises
        ------
        RuntimeError
            If the class reaches an invalid state lacking both a name and a path.
        """
        if self.mne_name:
            return make_standard_montage(self.mne_name)
        elif self.path:
            return read_custom_montage(self.path)

        raise RuntimeError(
            "Invalid state: Montage requires either 'mne_name' or 'path'."
        )


class EEGChanSpec(BaseModel):
    """
    Configuration for the EEG electrode array and referencing.

    Defines the physical properties of the EEG acquisition, including the
    number of sensors, their spatial arrangement, and the electrical
    referencing scheme.
    """

    number: PositiveInt
    montage: Montage
    ground: str
    reference: str | Literal["VARIES"]


class AuxChanSpec(BaseModel):
    """
    Metadata specification for auxiliary channels.

    Defines how non-EEG channels (e.g., ECG, triggers, or motion sensors)
    should be categorized in both MNE and BIDS, including their physical
    units and sensor locations.
    """

    mne_type: MNEChanTypes
    bids_type: BIDSChanTypes
    description: str | None = None  # Optional
    units: str | None = None  # Optional
    location: (
        str | dict[str, str]
    )  # Leaving the location dict relatively free-form here


class AcceptableImpedance(BaseModel):
    """Threshold and units for acceptable sensor impedance levels."""

    value: int
    units: str


class LightingConditions(BaseModel):
    """Environmental lighting metadata for the recording session."""

    description: str
    measurement: str


class FilterSpec(BaseModel):
    """Configuration for signal filters applied to the dataset."""

    name: str
    type: FilterTypeOptions
    info: dict[
        str, Any
    ]  # This dict will be copied directly to the eeg sidecar, so should contain that info directly


class ExtraSpec(BaseModel):
    """Optional metadata for experimental environment and recording quality."""

    acceptable_impedance: AcceptableImpedance | None = None
    electrode_type: str | None = None
    conductive_medium: str | None = None
    faraday_cage: bool | None = None
    sound_proof: bool | None = None
    lighting_conditions: LightingConditions | None = None


class AcquisitionSpecs(BaseModel):
    """
    Comprehensive hardware and software specifications for a recording.

    Aggregates channel configurations, filter settings, and environmental
    details into a single schema used to populate BIDS sidecar files.
    """

    software: str
    acquisition_freq: PositiveInt
    file_format: str
    amplifier_model: str
    eeg_channels: EEGChanSpec
    aux_channels: dict[str, AuxChanSpec]
    power_line_freq: LineFreqOptions
    filters: list[FilterSpec]
    extras: ExtraSpec | None = None


class BaseRestingTask(BaseModel):
    """Core duration requirements for a resting state segment."""

    duration_secs: PositiveInt


class RestingStateTask(BaseRestingTask):
    """Standard resting state condition with optional stimulus info."""

    stimulus_description: str | None = None


class CustomRestingTask(BaseRestingTask):
    """Named resting state condition with required stimulus description."""

    condition_name: str
    stimulus_description: str


class RestingStateProtocol(BaseModel):
    """
    Comprehensive resting state protocol and event mapping.

    Defines instructions, standard conditions, and custom segments,
    along with a dictionary mapping trigger codes to event descriptions.
    """

    instructions: str
    eyes_open: RestingStateTask | Literal[False]
    eyes_closed: RestingStateTask | Literal[False]
    other_conditions: list[CustomRestingTask] | None = None
    events: dict[str, str]  # Should be defined as "event code": "event description"


class DescriptionSpec(BaseModel):
    """
    Root schema for the machine-readable dataset description.

    Aggregates global metadata, acquisition hardware settings,
    resting-state protocols, and logic for handling subject-variable fields.
    """

    metadata: DatasetMetadata
    conditions: list[str] | None = Field(default=None, min_length=1)
    acquisition_spec: AcquisitionSpecs
    resting_state: RestingStateProtocol
    variable_fields: dict[str, str] | None = Field(default=None)

    @property
    def crawler_info(self):
        """Metadata for the directory crawler to filter files."""
        return {
            "expected_conditions": self.conditions,
            "extension": self.acquisition_spec.file_format,
        }

    @classmethod
    def from_template(
        cls,
        template: Self,
        varies_paths: list,
        subject_info: SubjectMetadata,
    ) -> Self:
        """
        Create a subject-specific specification from a base template.

        Parameters
        ----------
        template : Self
            The base configuration model to use as a template.
        varies_paths : list of list of str
            Nested dictionary paths to fields requiring dynamic updates.
        subject_info : SubjectMetadata
            Source object containing subject-specific values to inject.

        Returns
        -------
        Self
            A new instance of DescriptionSpec with resolved variable fields.
        """
        subject_spec = template.model_dump()

        if (var_fields := subject_spec.get("variable_fields")) is not None:
            for path in varies_paths:
                item_key = path[-1]
                subject_loc_key = var_fields[item_key]
                subject_value = getattr(subject_info, subject_loc_key)

                logger.info(
                    f"Updating variable metadata: {'.'.join(path)} = {subject_value}"
                )

                apply_dynamic_value(subject_spec, path, subject_value)

        return cls.model_validate(subject_spec)
