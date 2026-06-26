import logging
from enum import IntEnum, StrEnum
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


class MNEChanTypes(StrEnum):
    """
    Standard channel types recognised by MNE-Python.

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


class BIDSChanTypes(StrEnum):
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
    """Supported power-line frequencies for MNE and BIDS metadata."""

    FIFTY = 50
    SIXTY = 60


class EthicsApprovalOptions(StrEnum):
    """Status options for institutional ethical approval."""

    APPROVED = "Approved"
    NOT_REQUIRED = "Not Required"


class FilterTypeOptions(StrEnum):
    """Options for different online filtering sources."""

    HARDWARE = "Hardware"
    SOFTWARE = "Software"


class DatasetMetadata(BaseModel):
    """
    Schema for top-level BIDS dataset metadata.

    Defines the global information required for the dataset description,
    including institutional details, funding, and ethical approval status.
    This model ensures that the dataset-level requirements for BIDS
    compliance are met before export.

    Attributes
    ----------
    population : str
        A description of the study population (e.g., 'healthy adults').
    dataset_name : str
        The full name of the dataset.
    authors : list[str]
        List of individuals who contributed to the creation of the dataset.
    funding : str | list[str] | None, optional
        Funding sources or grant numbers associated with the study.
    ethics_approval : EthicsApprovalOptions
        The institutional review board or ethics committee approval status.
    license : str
        The data license (e.g., 'CC0', 'PDDL') under which the data is shared.
    references_links : str | list[str]
        Citations or URLs to publications or repositories related to the data.
    institution_name : str
        The name of the university or research facility where data was collected.
    institution_dept : str
        The specific department within the institution.
    """

    population: str
    dataset_name: str
    authors: list[str]
    funding: str | list[str] | None = None
    ethics_approval: EthicsApprovalOptions
    license: str
    references_links: list[str] | None = None
    institution_name: str
    institution_dept: str

    def create_dict(self) -> dict:
        """
        Generate a dictionary formatted for BIDS dataset_description.json.

        Maps internal model fields to their official BIDS-compliant keys
        as defined in the BIDS specification. This dictionary can be
        serialized directly to JSON.

        Returns
        -------
        dict
            A dictionary containing the standardised BIDS metadata keys
            (e.g., 'Name', 'Authors', 'DatasetDOI').
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
        must be a recognised string in MNE's built-in montages.
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
            raise ValueError("Only one of either 'mne_name' or 'path' fields need to be provided")

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

        raise RuntimeError("Invalid state: Montage requires either 'mne_name' or 'path'.")


class EEGChanSpec(BaseModel):
    """
    Configuration for the EEG electrode array and referencing.

    Defines the physical properties of the EEG acquisition, including the
    number of sensors, their spatial arrangement, and the electrical
    referencing scheme used during the recording.

    Attributes
    ----------
    number : PositiveInt
        Total count of EEG channels present in the recording.
    montage : Montage
        The spatial layout or naming convention of the electrodes, see
        the Montage class for more information.
    ground : str
        The physical location of the ground electrode (e.g., 'AFz', 'Fz').
    reference : str | Literal["VARIES"]
        The electrical reference used. Can be a specific electrode location
        (e.g., 'Cz', 'Average') or "VARIES" if the reference is inconsistent
        across the dataset or subject to offline changes.
    """

    number: PositiveInt
    montage: Montage
    ground: str
    reference: str | Literal["VARIES"]


class AuxChanSpec(BaseModel):
    """
    Metadata specification for auxiliary channels.

    Defines how non-EEG channels are categorised for MNE and BIDS,
    including their physical units and anatomical sensor locations.
    This model facilitates channel renaming and retyping during the
    BIDS conversion process.

    Attributes
    ----------
    mne_type : MNEChanTypes
        The channel type designation used by MNE-Python
        (e.g., 'ecg', 'emg', 'stim').
    bids_type : BIDSChanTypes
        The BIDS channel type (e.g., 'TRIG', 'MISC', 'EYE').
    description : str | None, optional
        A human-readable description of the channel's purpose or source.
    units : str | None, optional
        The physical unit of the signal (e.g., 'V', 'uV', 'mmHg').
    location : str | dict[str, str]
        Anatomical placement of the sensors. Can be a descriptive string
        (e.g., 'left index finger'), "n/a", or a dictionary defining the
        specific lead configuration (e.g., active, reference, and ground
        placements)
    """

    mne_type: MNEChanTypes
    bids_type: BIDSChanTypes
    description: str | None = None  # Optional
    units: str | None = None  # Optional
    location: str | dict[str, str]  # Leaving the location dict relatively free-form here


class AcceptableImpedance(BaseModel):
    """
    Threshold and units for acceptable sensor impedance levels.

    Defines the maximum impedance value permitted for sensors during
    the recording session.

    Attributes
    ----------
    value : int
        The maximum impedance threshold (e.g., 5, 20).
    units : str
        The unit of measurement for the impedance value,
        typically 'kOhm'.
    """

    value: int
    units: str


class LightingConditions(BaseModel):
    """
    Environmental lighting metadata for the recording session.

    Captures the ambient lighting state and intensity of the experimental
    room during data acquisition.

    Attributes
    ----------
    description : str
        A qualitative description of the lighting source or state
        (e.g., 'dimmed', 'natural light', 'fluorescent').
    measurement : str, optional
        The quantitative value and the method or instrument used for
        the reading (e.g., '150 lux via T-10A Illuminance Meter',
        'low via subjective report').
    """

    description: str
    measurement: str | None = None


class FilterSpec(BaseModel):
    """
    Configuration for signal filters applied to the dataset.

    Defines the parameters and origin of a specific filter, intended
    for direct inclusion in the BIDS EEG sidecar metadata.

    Attributes
    ----------
    name : str
        The descriptive name of the filter (e.g., 'High-pass', 'Notch').
    type : FilterTypeOptions
        The source of the filter application, either hardware or software.
    info : dict[str, Any]
        A dictionary of filter parameters (e.g., cut-off frequencies,
        roll-off, order). This content is mapped directly to the BIDS
        EEG sidecar JSON.
    """

    name: str
    type: FilterTypeOptions
    info: dict[str, Any]  # This dict will be copied directly to the eeg sidecar, so should contain that info directly


class ExtraSpec(BaseModel):
    """
    Optional metadata for experimental environment and recording quality.

    Groups secondary environmental factors and technical hardware
    specifications that characterise the recording conditions.

    Attributes
    ----------
    acceptable_impedance : AcceptableImpedance | None, optional
        The threshold and units used to define valid sensor impedance.
    electrode_type : str | None, optional
        The type of electrodes used (e.g., 'active', 'passive', 'Ag/AgCl').
    conductive_medium : str | None, optional
        The material used to reduce impedance (e.g., 'gel', 'paste', 'saline').
    faraday_cage : bool | None, optional
        Whether the recording was performed inside a Faraday cage.
    sound_proof : bool | None, optional
        Whether the recording was performed in a sound-attenuated booth.
    lighting_conditions : LightingConditions | None, optional
        The ambient lighting state and intensity of the experimental room.
    """

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

    Attributes
    ----------
    software : str
        The name and version of the software used to acquire the data
        (e.g., 'LabRecorder v1.14', 'OpenBCI GUI').
    acquisition_freq : PositiveInt
        The sampling rate of the recording in Hertz (Hz).
    file_format : str
        The format of the raw data file (e.g., 'BDF', 'EDF', 'FIFF').
    amplifier_model : str
        The manufacturer and model of the EEG amplifier
        (e.g., 'BioSemi ActiveTwo', 'BrainAmp Standard').
    eeg_channels : EEGChanSpec
        Specifications for the EEG electrode array and referencing scheme.
    aux_channels : dict[str, AuxChanSpec]
        A mapping of auxiliary channel names to their respective types,
        units, and locations.
    power_line_freq : LineFreqOptions
        The frequency of the local electrical grid (e.g., 50 or 60 Hz).
    filters : list[FilterSpec]
        A list of hardware and software filters applied during acquisition.
    extras : ExtraSpec | None, optional
        Additional environmental and hardware metadata, such as lighting
        and impedance thresholds.
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
    """
    Core duration requirements for a resting state segment.

    Attributes
    ----------
    duration_secs : PositiveInt
        The required length of the resting state recording in seconds.
    """

    duration_secs: PositiveInt


class RestingStateTask(BaseRestingTask):
    """
    Standard resting state condition with optional stimulus info.

    Inherits core duration requirements and allows for an optional
    description of the resting environment or instructions.

    Attributes
    ----------
    duration_secs : PositiveInt
        The required length of the resting state recording in seconds.
    stimulus_description : str | None, optional
        Details regarding the resting state protocol (e.g., 'eyes closed',
        'fixation cross').
    """

    stimulus_description: str | None = None


class CustomRestingTask(BaseRestingTask):
    """
    Named resting state condition with required stimulus description.

    Used for non-standard resting segments that require a specific
    condition label and mandatory stimulus details.

    Attributes
    ----------
    duration_secs : PositiveInt
        The required length of the resting state recording in seconds.
    condition_name : str
        The unique identifier for the custom task (e.g., 'meditation',
        'pre-task-rest').
    stimulus_description : str
        Mandatory details regarding the specific instructions or
        environment for this custom condition.
    """

    condition_name: str
    stimulus_description: str


class RestingStateProtocol(BaseModel):
    """
    Comprehensive resting state protocol and event mapping.

    Defines instructions, standard conditions, and custom segments,
    along with a dictionary mapping trigger codes to event descriptions.

    Attributes
    ----------
    instructions : str
        The textual instructions provided to the participant prior to
        starting the resting state session.
    eyes_open : RestingStateTask | Literal[False]
        Configuration for the eyes-open segment. Set to False if this
        condition is not part of the protocol.
    eyes_closed : RestingStateTask | Literal[False]
        Configuration for the eyes-closed segment. Set to False if this
        condition is not part of the protocol.
    other_tasks : list[CustomRestingTask] | None, optional
        A list of additional resting state conditions or segments
        not covered by the standard eyes-open/closed categories.
    events : dict[str, str]
        A mapping of hardware trigger codes to human-readable labels
        (e.g., {"1": "eyes_open_start", "2": "eyes_closed_start"}).
    """

    instructions: str
    eyes_open: RestingStateTask | Literal[False]
    eyes_closed: RestingStateTask | Literal[False]
    other_tasks: list[CustomRestingTask] | None = None
    events: dict[str, str]  # Should be defined as "event code": "event description"


class DescriptionSpec(BaseModel):
    """
    Root schema for the machine-readable dataset description.

    Aggregates global metadata, acquisition hardware settings,
    resting-state protocols, and logic for handling subject-variable fields.
    This serves as the primary configuration object for BIDS conversion
    and directory crawling.

    Attributes
    ----------
    metadata : DatasetMetadata
        Global dataset information including funding, authors, and ethics.
    conditions : list[str] | None, optional
        A list of experimental task or condition names. Aliased as 'tasks'
        in the input data.
    acquisition_spec : AcquisitionSpecs
        Hardware and software technical specifications for the recording.
    resting_state : RestingStateProtocol
        The protocol definition and event mapping for resting segments.
    variable_fields : dict[str, str] | None, optional
        A mapping of specification keys to subject-level metadata fields
        used for dynamic value injection.
    """

    metadata: DatasetMetadata
    conditions: list[str] | None = Field(default=None, min_length=1, alias="tasks")
    acquisition_spec: AcquisitionSpecs
    resting_state: RestingStateProtocol
    variable_fields: dict[str, str] | None = Field(default=None)

    @property
    def crawler_info(self) -> dict:
        """
        Metadata for the directory crawler to filter and identify files.

        Returns
        -------
        dict
            A dictionary containing 'expected_conditions' and the target
            file 'extension'.
        """
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

        Iterates through designated paths in the configuration and replaces
        placeholder or generic values with specific metadata associated
        with an individual participant.

        Parameters
        ----------
        template : Self
            The base configuration model used as the structural template.
        varies_paths : list of list of str
            A list of nested dictionary paths (e.g., [['acquisition_spec', 'software']])
            indicating which fields require dynamic updates.
        subject_info : SubjectMetadata
            The source object containing the actual participant values to
            be injected into the template.

        Returns
        -------
        Self
            A new instance of DescriptionSpec with all variable fields
            resolved to subject-specific values.
        """
        subject_spec = template.model_dump()

        if (var_fields := subject_spec.get("variable_fields")) is not None:
            for path in varies_paths:
                item_key = path[-1]
                subject_loc_key = var_fields[item_key]
                subject_value = getattr(subject_info, subject_loc_key)

                if subject_value is None:
                    logger.error(f"Value for variable metadata {'.'.join(path)} not present")
                    raise ValueError
                else:
                    logger.debug(f"Updating variable metadata: {'.'.join(path)} = {subject_value}")
                    apply_dynamic_value(subject_spec, path, subject_value)

        return cls.model_validate(subject_spec)
