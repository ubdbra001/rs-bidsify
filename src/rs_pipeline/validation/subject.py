from datetime import datetime, date, timedelta, timezone
from enum import IntEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, ValidationInfo, computed_field, PositiveInt

from rs_pipeline.config import DEMOGRAPHIC_MAPPINGS as MAPPINGS

def get_utc_today() -> datetime:
    return datetime.now(timezone.utc)

class SubjectMetadata(BaseModel):
    age: PositiveInt = Field(exclude=True)
    sex: Literal[0, 1, 2]
    hand: Literal[1, 2, 3] = Field(alias="handedness")
    meas_date: datetime = Field(default_factory=get_utc_today, exclude=True)

    @field_validator("sex", "hand", mode="before")
    @classmethod
    def map_string_to_int(cls, value: Any, info: ValidationInfo) -> Any:
        if isinstance(value, str):
            val_lower = value.lower()
            
            mapping_dict = MAPPINGS.get(info.field_name, {})  # ty:ignore[no-matching-overload]
            
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
        meas_date = self.meas_date.date()
        try:
            return meas_date.replace(year=meas_date.year - self.age)
        except ValueError:
            return meas_date.replace(year=meas_date.year - self.age, day=28)

    def __str__(self) -> str:
        return f"Age = {self.age}, Birthday = {self.birthday.strftime('%d/%m/%y')}, Sex = {self.sex}, Hand = {self.hand}"