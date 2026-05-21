import pytest
from pathlib import Path
from pydantic import ValidationError

from rs_bidsify.validation import description as rs_desc


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

    @pytest.mark.xfail
    def test_valid_path(self, shared_file):
        data = {"path": shared_file}
        model = rs_desc.Montage(**data)

        assert model.mne_name is None
        assert model.path == shared_file

    def test_missing_path(self):
        data = {"path": "missing.file"}

        with pytest.raises(ValidationError):
            rs_desc.Montage.model_validate(data)

    @pytest.mark.xfail
    def test_both_present(self, shared_file):
        data = {"mne_name": "standard_1020", "path": shared_file}

        with pytest.raises(ValidationError):
            rs_desc.Montage(**data)

    def test_both_missing(self):
        with pytest.raises(ValidationError):
            rs_desc.Montage(mne_name=None, path=None)
