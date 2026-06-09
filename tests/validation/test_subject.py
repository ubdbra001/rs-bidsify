from datetime import date, datetime

import pandas as pd
import pytest

from rs_bidsify.validation.dataset import RecordingMetadata
from rs_bidsify.validation.subject import SubjectMetadata


@pytest.fixture
def base_context_mapping():
    return {
        "mappings": {
            "sex": {"m": 1, "f": 2, "o": 0},
            "hand": {"right": 1, "left": 2, "ambi": 3},
        }
    }


class TestSubjectMetadata:
    def test_valid_initialization(self):
        """Test standard initialization with correct data types."""
        data = {"age": 25, "sex": 1, "handedness": 2}
        subject = SubjectMetadata(**data)  # type: ignore

        assert subject.age == 25
        assert subject.sex == 1
        assert subject.hand == 2
        assert isinstance(subject.meas_date, datetime)

    def test_extra_fields_allowed(self):
        """Test that extra fields are permitted due to ConfigDict(extra='allow')."""
        data = {
            "age": 30,
            "sex": 0,
            "handedness": 3,
            "favorite_color": "blue",  # Extra field
        }
        subject = SubjectMetadata(**data)

        assert getattr(subject, "favorite_color") == "blue"  # noqa

    @pytest.mark.parametrize(
        "input_data, expected_sex, expected_hand",
        [
            pytest.param({"age": 30, "sex": "m", "handedness": "right"}, 1, 1, id="lower case vals"),
            pytest.param({"age": 30, "sex": "M", "handedness": "RigHt"}, 1, 1, id="mixed case vals"),
        ]
    )
    def test_string_to_int_mapping_valid(self, input_data, expected_sex, expected_hand, base_context_mapping):
        """Test the @field_validator correctly maps string aliases to ints via context."""

        subject = SubjectMetadata.model_validate(input_data, context=base_context_mapping)

        assert subject.sex == expected_sex
        assert subject.hand == expected_hand

    def test_string_to_int_mapping_invalid(self, base_context_mapping):
        """Test that SubjectMetadata class rases an error when invalid string passed"""
        data = {"age": 30, "sex": "m", "handedness": "r"}

        with pytest.raises(ValueError, match = "Unrecognized string"):
           SubjectMetadata.model_validate(data, context=base_context_mapping)

    @pytest.mark.parametrize(
        "meas_date, exp_birthday, age",
        [
            pytest.param(datetime(2023, 5, 15), date(1998, 5, 15), 25, id="normal-calc"),
            pytest.param(datetime(2024, 2, 29), date(1999, 2, 28), 25, id="leap-to-non-leap-year-calc"),
            pytest.param(datetime(2024, 2, 29), date(2000, 2, 29), 24, id="leap-to-leap-year-calc"),
        ],
    )
    def test_birthday_computation(self, meas_date, exp_birthday, age):
        """Test standard birthday computation."""
        subject = SubjectMetadata(age=age, sex=1, handedness=1, meas_date=meas_date)

        assert subject.birthday == exp_birthday

    def test_subject_info_dump(self):
        """Test that the model dump strictly includes only the specified 3 keys."""
        subject = SubjectMetadata(age=20, sex=2, handedness=3)
        dump = subject.subject_info_dump()

        assert set(dump.keys()) == {"sex", "hand", "birthday"}
        assert dump["sex"] == 2
        assert dump["hand"] == 3
        assert dump["birthday"] == subject.birthday

    def test_str_representation(self):
        """Test the __str__ method formats the output properly."""
        meas_date = datetime(2023, 10, 10)
        subject = SubjectMetadata(age=20, sex=1, handedness=2, meas_date=meas_date)

        expected_str = "Age = 20, Birthday = 10/10/03, Sex = 1, Hand = 2"
        assert str(subject) == expected_str

    @pytest.mark.parametrize(
        "sub_id, exp_age, exp_sex, exp_hand",
        [
            ("sub-01", 25, 1, 1),
            ("sub-02", 40, 2, 2),
        ],
    )
    def test_from_dataframe(self, base_context_mapping, sub_id, exp_age, exp_sex, exp_hand):
        """Test extraction and instantiation from a pandas DataFrame."""
        # Setup mock dataframe
        df = pd.DataFrame(
            {"age": [25, 40], "sex": ["m", "f"], "handedness": ["right", "left"]},
            index=["sub-01", "sub-02"],
        )

        recording = RecordingMetadata.model_construct(participant=sub_id)

        subject = SubjectMetadata.from_dataframe(recording=recording, df=df, mapping=base_context_mapping["mappings"])

        assert subject.age == exp_age
        assert subject.sex == exp_sex
        assert subject.hand == exp_hand

    def test_from_dataframe_missing_participant(self, base_context_mapping):
        """Test that from_dataframe raises a KeyError if the participant is not in the DataFrame index."""
        df = pd.DataFrame(
            {"age": [25, 40], "sex": ["m", "f"], "handedness": ["right", "left"]},
            index=["sub-01", "sub-02"],
        )

        recording = RecordingMetadata.model_construct(participant="sub-99")

        with pytest.raises(KeyError) as exc_info:
            SubjectMetadata.from_dataframe(
                recording=recording, 
                df=df, 
                mapping=base_context_mapping["mappings"]
            )

        assert "sub-99" in str(exc_info.value)

    def test_from_dataframe_missing_column(self, base_context_mapping):
        """Test that from_dataframe raises a KeyError if expected column is not in the DataFrame."""
        df = pd.DataFrame(
            {"age": [25, 40], "sex": ["m", "f"]},
            index=["sub-01", "sub-02"],
        )

        recording = RecordingMetadata.model_construct(participant="sub-01")

        with pytest.raises(ValueError):
            SubjectMetadata.from_dataframe(
                recording=recording, 
                df=df, 
                mapping=base_context_mapping["mappings"]
            )
            