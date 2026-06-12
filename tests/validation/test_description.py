from pathlib import Path

import pytest

from rs_bidsify.validation import description as rs_desc
from rs_bidsify.validation.subject import SubjectMetadata


@pytest.fixture
def shared_file(fs) -> Path:
    file_path = Path("data") / "test_file.loc"
    fs.create_file(file_path, contents="dummy content")
    return file_path


class TestMontageInfo:
    def test_valid_name(self):
        data = {"mne_name": "standard_1020"}
        model = rs_desc.Montage.model_validate(data)

        assert model.mne_name == data["mne_name"]
        assert model.path is None

    def test_invalid_name(self):
        data = {"mne_name": "not_a_real_montage"}
        with pytest.raises(ValueError, match="is not a valid built-in MNE montage"):
            rs_desc.Montage.model_validate(data)

    def test_valid_path(self, shared_file):
        data = {"path": shared_file}
        model = rs_desc.Montage.model_validate(data)

        assert model.mne_name is None
        assert model.path == shared_file

    def test_both_present(self, shared_file):
        data = {"mne_name": "standard_1020", "path": shared_file}

        with pytest.raises(ValueError, match="Only one of either"):
            rs_desc.Montage(**data)

    def test_both_missing(self):
        with pytest.raises(ValueError, match="Need to provide either"):
            rs_desc.Montage(mne_name=None, path=None)

    def test_montage_property_logic(self, mocker, shared_file):
        mock_make = mocker.patch("rs_bidsify.validation.description.make_standard_montage")
        mock_read = mocker.patch("rs_bidsify.validation.description.read_custom_montage")

        data_name = {"mne_name": "standard_1020"}
        m_builtin = rs_desc.Montage.model_validate(data_name)

        _ = m_builtin.montage
        mock_make.assert_called_once_with("standard_1020")

        custom_file = shared_file
        data_path = {"path": custom_file}
        m_custom = rs_desc.Montage.model_validate(data_path)
        _ = m_custom.montage
        mock_read.assert_called_once_with(custom_file)

    def test_montage_property_is_cached(self, mocker):
        mock_make = mocker.patch("rs_bidsify.validation.description.make_standard_montage")
        m = rs_desc.Montage.model_validate({"mne_name": "standard_1020"})

        _ = m.montage
        _ = m.montage
        _ = m.montage

        assert mock_make.call_count == 1


class TestDescriptionSpecTemplate:
    def test_from_template_happy_path(self, mocker):
        """Test that dynamic fields are correctly injected from SubjectMetadata into the template."""

        mock_template_dict = {
            "acquisition_spec": {"software": "DEFAULT_SOFTWARE"},
            "variable_fields": {"software": "subject_software_version"},
        }

        mock_template = mocker.MagicMock()
        mock_template.model_dump.return_value = mock_template_dict

        mock_subject_info = mocker.MagicMock(spec=SubjectMetadata)
        mock_subject_info.subject_software_version = "BrainVision v2.0"

        varies_paths = [["acquisition_spec", "software"]]

        mock_apply = mocker.patch("rs_bidsify.validation.description.apply_dynamic_value")

        mocker.patch.object(rs_desc.DescriptionSpec, "model_validate", return_value="Success")

        result = rs_desc.DescriptionSpec.from_template(mock_template, varies_paths, mock_subject_info)

        assert result == "Success"

        mock_apply.assert_called_once_with(mock_template_dict, ["acquisition_spec", "software"], "BrainVision v2.0")

    def test_from_template_missing_subject_value_raises_error(self, mocker):
        """Test that a ValueError is raised if the required subject attribute resolves to None."""
        mock_template_dict = {
            "acquisition_spec": {"software": "DEFAULT_SOFTWARE"},
            "variable_fields": {"software": "subject_software_version"},
        }

        mock_template = mocker.MagicMock()
        mock_template.model_dump.return_value = mock_template_dict

        mock_subject_info = mocker.MagicMock(spec=SubjectMetadata)
        mock_subject_info.subject_software_version = None

        varies_paths = [["acquisition_spec", "software"]]

        with pytest.raises(ValueError):
            rs_desc.DescriptionSpec.from_template(mock_template, varies_paths, mock_subject_info)
