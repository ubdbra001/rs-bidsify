from pydantic import ValidationError
from pathlib import Path

import pytest

from rs_pipeline.validation.dataset import RecordingMetadata, EEGDatasetCrawler


class TestRecordingMetadata:
    def test_recording_path_resolves(self, fs):
        fake_file = Path("/data/sub-01/ses-01/sub-01.eeg")
        fs.create_file(fake_file)

        rec = RecordingMetadata(
            participant="sub-01", condition=None, session="ses-01", path=fake_file
        )

        assert isinstance(rec.path, Path)
        assert str(rec.path) == str(fake_file)

    def test_recording_path_fails_on_missing_file(self):
        fake_file = Path("/non/existent/file.eeg")
        with pytest.raises(ValidationError):
            RecordingMetadata(
                participant="sub-01", condition=None, session=None, path=fake_file
            )

    @pytest.mark.parametrize(
        "cond, sess",
        [
            (None, None),
            ("rest", None),
            (None, "ses-01"),
            ("task", "ses-01"),
        ],
    )
    def test_recording_path_optional_fields(self, fs, cond, sess):
        path = Path("/data/test.eeg")
        fs.create_file(path)

        rec = RecordingMetadata(
            participant="sub-01", condition=cond, session=sess, path=path
        )
        assert rec.condition == cond
        assert rec.session == sess


class TestEEGDatasetCrawler:
    @pytest.mark.parametrize(
        "cond, sess, path_template",
        [
            (None, None, "sub-01/sub-01.eeg"),
            ("rest", None, "sub-01/rest/sub-01.eeg"),
            (None, "ses-01", "sub-01/ses-01/sub-01.eeg"),
            ("rest", "ses-01", "sub-01/rest/ses-01/sub-01.eeg"),
        ],
    )
    def test_correct_nesting(self, fs, cond, sess, path_template):
        full_path = Path("/data") / path_template
        fs.create_file(full_path)

        config = {
            "root_path": "/data",
            "expected_participants": ["sub-01"],
            "expected_conditions": [cond] if cond else None,
            "expected_sessions": [sess] if sess else None,
            "extension": ".eeg",
        }

        model = EEGDatasetCrawler(**config)

        res = model.found_recordings
        assert len(res) == 1
        assert res[0].condition == cond
        assert res[0].session == sess
        assert str(res[0].path) == str(full_path)

    @pytest.mark.parametrize(
        "cond, sess, path_template",
        [
            ("rest", None, "sub-01/sub-01.eeg"),
            ("rest", None, "sub-01/ses-01/sub-01.eeg"),
            (None, "ses-01", "sub-01/sub-01.eeg"),
            (None, "ses-01", "sub-01/rest/sub-01.eeg"),
            ("rest", "ses-01", "sub-01/sub-01.eeg"),
            ("rest", "ses-01", "sub-01/ses-01/rest/sub-01.eeg"),
        ],
    )
    def test_incorrect_nesting(self, fs, cond, sess, path_template):
        full_path = Path("/data") / path_template
        fs.create_file(full_path)

        config = {
            "root_path": "/data",
            "expected_participants": ["sub-01"],
            "expected_conditions": [cond] if cond else None,
            "expected_sessions": [sess] if sess else None,
            "extension": ".eeg",
        }

        with pytest.raises(ValidationError):
            EEGDatasetCrawler(**config)

    @pytest.mark.parametrize(
        "file_list", [(["sub-01.eeg"]), (["sub-01.eeg", "readme.txt"])]
    )
    def test_valid_single_leaf_rule(self, fs, file_list):
        for file in file_list:
            fs.create_file(Path("/data/sub-01") / file)

        config = {
            "root_path": "/data",
            "expected_participants": ["sub-01"],
            "extension": ".eeg",
        }

        model = EEGDatasetCrawler(**config)

        assert len(model.found_recordings) == 1

    @pytest.mark.parametrize(
        "file_list", [(["sub-01.txt"]), (["sub-01.eeg", "readme.eeg"])]
    )
    def test_invalid_single_leaf_rule(self, fs, file_list):
        for file in file_list:
            fs.create_file(Path("/data/sub-01") / file)

        config = {
            "root_path": "/data",
            "expected_participants": ["sub-01"],
            "extension": ".eeg",
        }

        with pytest.raises(ValidationError):
            EEGDatasetCrawler(**config)

    def test_expected_participants(self, fs, file_list):
        config = {
            "root_path": "/data",
            "expected_participants": ["sub-01", "sub-02", "sub-03"],
            "extension": ".eeg",
        }

        for p_id in config["expected_participants"]:
            fs.create_file(Path("/data") / p_id / f"{p_id}.eeg")

        model = EEGDatasetCrawler(**config)
        assert len(model.found_recordings) == 3

    def test_missing_participants(self, fs):
        config = {
            "root_path": "/data",
            "expected_participants": ["sub-01", "sub-02", "sub-03"],
            "extension": ".eeg",
        }

        for p_id in config["expected_participants"][1:]:
            fs.create_file(Path("/data") / p_id / f"{p_id}.eeg")

        with pytest.raises(ValidationError):
            EEGDatasetCrawler(**config)
