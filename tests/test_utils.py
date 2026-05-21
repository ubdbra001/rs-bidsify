import logging
from datetime import UTC, datetime

import pytest

from rs_bidsify import utils


def test_get_utc_today(mocker):
    fake_now = datetime(2026, 5, 21, 12, 0, 0, tzinfo=UTC)

    mock_datetime = mocker.patch("rs_bidsify.utils.datetime")
    mock_datetime.now.return_value = fake_now

    result = utils.get_utc_today()

    assert result == fake_now
    assert result.tzinfo == UTC

    mock_datetime.now.assert_called_once_with(UTC)


class TestLocateDynamicFields:
    def test_locate_no_target(self):
        """Ensure it returns an empty list if the target isn't found."""
        data = {"a": 1, "b": {"c": 2}}
        assert utils.locate_dynamic_fields(data, target="VARIES") == []

    def test_locate_flat_dict(self):
        """Test finding a target at the top level."""
        data = {"a": "VARIES", "b": 2}
        assert utils.locate_dynamic_fields(data) == [["a"]]

    def test_locate_nested_multiple(self):
        """Test finding multiple targets at different depths."""
        data = {
            "subject": "VARIES",
            "session": {"date": "2024-01-01", "time": "VARIES"},
            "notes": "all good",
        }
        expected = [["subject"], ["session", "time"]]
        assert utils.locate_dynamic_fields(data) == expected

    def test_locate_empty_input(self):
        """Ensure it handles empty dictionaries."""
        assert utils.locate_dynamic_fields({}) == []


class TestApplyDynamicValue:
    def test_apply_success_nested(self):
        """Verify standard path traversal and value insertion."""
        data = {"a": {"b": {"c": "old"}}}
        path = ["a", "b", "c"]
        utils.apply_dynamic_value(data, path, "new")

        assert data["a"]["b"]["c"] == "new"

    def test_apply_adds_new_key(self):
        """Verify it can add a new key if the parent path exists."""
        data = {"a": {"b": {}}}
        path = ["a", "b", "d"]
        utils.apply_dynamic_value(data, path, "inserted")

        assert data["a"]["b"]["d"] == "inserted"

    def test_apply_key_error_preserves_traceback(self, caplog):
        """Verify a KeyError is re-raised and the path is logged."""
        data = {"a": {"b": 1}}
        path = ["a", "missing_key", "c"]

        with caplog.at_level(logging.ERROR), pytest.raises(KeyError):
            utils.apply_dynamic_value(data, path, "value")

        assert f"Path {'.'.join(path)} could not be followed" in caplog.text

    def test_apply_type_error_preserves_traceback(self, caplog):
        """Verify a TypeError is re-raised when indexing into an int."""
        data = {"a": 100}
        path = ["a", "b"]

        with caplog.at_level(logging.ERROR), pytest.raises(TypeError):
            utils.apply_dynamic_value(data, path, "value")

        assert f"Path {'.'.join(path)} could not be followed" in caplog.text
