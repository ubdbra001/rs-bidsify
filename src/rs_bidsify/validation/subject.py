from datetime import datetime, date
from typing import Any, Literal, Self

from pandas import DataFrame
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    ValidationInfo,
    computed_field,
    PositiveInt,
    ConfigDict,
)

from rs_bidsify.validation.dataset import RecordingMetadata
from rs_bidsify.utils import get_utc_today


class SubjectMetadata(BaseModel):
    """
    Data model for participant demographic information.

    Handles the conversion of human-readable strings (e.g., 'male', 'right')
    into BIDS-compliant integers and calculates a proxy birthday required
    by MNE for age internal calculations.

    Attributes
    ----------
    age : PositiveInt
        Participant age in years.
    sex : Literal[0, 1, 2]
        Participant biological sex (0=Unknown, 1=Male, 2=Female).
    hand : Literal[1, 2, 3]
        Participant handedness (1=Left, 2=Right, 3=Ambidextrous).
    meas_date : datetime
        The date of the recording, defaults to UTC today.
    """

    model_config = ConfigDict(extra="allow")

    age: PositiveInt
    sex: Literal[0, 1, 2]
    hand: Literal[1, 2, 3] = Field(alias="handedness")
    meas_date: datetime = Field(default_factory=get_utc_today)

    @field_validator("sex", "hand", mode="before")
    @classmethod
    def map_string_to_int(cls, value: Any, info: ValidationInfo) -> Any:
        """
        Convert sex and handedness strings to BIDS-compliant integers.

        Uses a mapping dictionary provided via validation context to translate
        strings like 'female' to their integer representation.
        """
        context = info.context or {}
        mapping_dict = context.get("mappings", {}).get(info.field_name, {})

        if isinstance(value, str):
            if (val_lower := value.lower()) in mapping_dict:
                return mapping_dict[val_lower]
            else:
                allowed_strings = ", ".join(f"'{k}'" for k in mapping_dict.keys())
                raise ValueError(
                    f"Unrecognized string '{value}' for {info.field_name}. "
                    f"Allowed string formats are: {allowed_strings}"
                )

        return value

    @computed_field
    @property
    def birthday(self) -> date:
        """
        Calculate a surrogate birthday based on age and measurement date.

        MNE requires a 'birthday' field to store age in its internal
        subject_info. This computes a date exactly 'age' years prior to
        the recording date.
        """
        meas_date = self.meas_date.date()
        try:
            return meas_date.replace(year=meas_date.year - self.age)
        except ValueError:
            return meas_date.replace(year=meas_date.year - self.age, day=28)

    def subject_info_dump(self):
        """
        Generate a dictionary formatted for MNE's info['subject_info'].

        Returns
        -------
        dict
            A dictionary containing only 'sex', 'hand', and 'birthday'.
        """
        return self.model_dump(include={"sex", "hand", "birthday"})

    def __str__(self) -> str:
        return f"Age = {self.age}, Birthday = {self.birthday.strftime('%d/%m/%y')}, Sex = {self.sex}, Hand = {self.hand}"

    @classmethod
    def from_dataframe(
        cls, recording: RecordingMetadata, df: DataFrame, mapping: dict[str, Any]
    ) -> Self:
        """
        Initialize the model using a row from a pandas DataFrame.

        Parameters
        ----------
        recording : RecordingMetadata
            Metadata for the current recording session, used to find
            the participant ID index.
        df : DataFrame
            The dataframe containing demographic data.
        mapping : dict[str, Any]
            Dictionaries defining string-to-int mappings for sex and hand.

        Returns
        -------
        SubjectMetadata
            A validated instance of the model.
        """
        subject_row = df.loc[recording.participant].to_dict()
        return cls.model_validate(**subject_row, context={"mappings": mapping})  # type: ignore
