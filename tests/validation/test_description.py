import pytest
from pydantic import ValidationError

from rs_bidsify.validation import description as rs_desc


class TestMontageInfo:
    @pytest.fixture(scope="class")
    def shared_file(self, tmp_path_factory):
        temp_dir = tmp_path_factory.mktemp("data")
        f = temp_dir / "test_file.loc"
        f.write_text("dummy content")
        return f

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
