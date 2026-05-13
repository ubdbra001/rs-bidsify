from datetime import datetime, date
from typing import Any, Literal

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

from rs_bidsify.config import DEMOGRAPHIC_MAPPINGS as MAPPINGS
from rs_bidsify.validation.dataset import RecordingMetadata
from rs_bidsify.utils import get_utc_today


class SubjectMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    age: PositiveInt
    sex: Literal[0, 1, 2]
    hand: Literal[1, 2, 3] = Field(alias="handedness")
    meas_date: datetime = Field(default_factory=get_utc_today)

    @field_validator("sex", "hand", mode="before")
    @classmethod
    def map_string_to_int(cls, value: Any, info: ValidationInfo) -> Any:
        """Convert sex and handedness strings to integers"""
        if isinstance(value, str):
            val_lower = value.lower()

            mapping_dict = MAPPINGS.get(info.field_name, {})  # type: ignore

            if val_lower in mapping_dict:
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
        """Compute faux birthday from age and current date"""
        meas_date = self.meas_date.date()
        try:
            return meas_date.replace(year=meas_date.year - self.age)
        except ValueError:
            return meas_date.replace(year=meas_date.year - self.age, day=28)

    def subject_info_dump(self):
        """Model dump only including items used in MNE subject_info dict"""
        return self.model_dump(include={"sex", "hand", "birthday"})

    def __str__(self) -> str:
        return f"Age = {self.age}, Birthday = {self.birthday.strftime('%d/%m/%y')}, Sex = {self.sex}, Hand = {self.hand}"
    
    @classmethod
    def from_dataframe(cls, recording: RecordingMetadata, df: DataFrame) -> SubjectMetadata:
        """Generates a SubjectMetadata class from a dataframe"""
        subject_row = df.loc[recording.participant].to_dict()
        return cls(**subject_row) #type: ignore

