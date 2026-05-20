import pytest
from unittest.mock import patch, mock_open
from rs_bidsify import config_loader


def test_get_default_config():
    mock_yaml = "test_key: test_value"
    with patch("importlib.resources.open_text", mock_open(read_data=mock_yaml)):
        config = config_loader.get_default_config()
        assert config == {"test_key": "test_value"}


@pytest.mark.parametrize(
    "base, overrides, expected",
    [
        ({"a": 1, "b": 2}, {"b": 3, "c": 4}, {"a": 1, "b": 3, "c": 4}),
        (
            {"nested": {"a": 1, "b": 2}},
            {"nested": {"b": 3}},
            {"nested": {"a": 1, "b": 3}},
        ),
        ({"a": 1}, {"a": {"nested": 2}}, {"a": {"nested": 2}}),
        ({"a": {"nested": 1}}, {"a": 2}, {"a": 2}),
    ],
)
def test_deep_merge(base, overrides, expected):
    result = config_loader.deep_merge(base, overrides)
    assert result == expected
