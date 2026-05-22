from pathlib import Path

import pytest
from pydantic import ValidationError

from rs_bidsify.validation.dataset import EEGDatasetCrawler, RecordingMetadata


class TestRecordingMetadata:
    def test_recording_path_resolves(self, fs):
        fake_file = Path("/data/sub-01/sub-01.eeg")
        fs.create_file(fake_file)

        rec = RecordingMetadata(participant="sub-01", condition=None, path=fake_file)

        assert isinstance(rec.path, Path)
        assert str(rec.path) == str(fake_file)

    def test_recording_path_fails_on_missing_file(self):
        fake_file = Path("/non/existent/file.eeg")
        with pytest.raises(ValidationError):
            RecordingMetadata(participant="sub-01", condition=None, path=fake_file)

    @pytest.mark.parametrize(
        "cond",
        [
            (None),
            ("rest"),
        ],
    )
    def test_recording_path_optional_fields(self, fs, cond):
        path = Path("/data/test.eeg")
        fs.create_file(path)

        rec = RecordingMetadata(participant="sub-01", condition=cond, path=path)
        assert rec.condition == cond

    @pytest.mark.parametrize(
        "participant, expected_subject",
        [
            ("sub-01", "01"),
            ("participant_A1", "A1"),
            ("001", "001"),
            ("experiment-group-S01", "S01"),
            ("sub-01-rest", "rest"),
            ("sub_01_session_A", "A"),
        ],
    )
    def test_subject_regex_extraction(self, fs, participant, expected_subject):
        path = Path("/data/test.eeg")
        fs.create_file(path)

        rec = RecordingMetadata(participant=participant, condition=None, path=path)

        assert rec.subject == expected_subject

    @pytest.mark.parametrize(
        "invalid_participant",
        [
            "sub-01!",
            "part_#1",
            "sub-01-",
            "!!!",
        ],
    )
    def test_subject_fails_on_non_alphanumeric(self, fs, invalid_participant):
        path = Path("/data/test.eeg")
        fs.create_file(path)

        rec = RecordingMetadata(participant=invalid_participant, condition=None, path=path)

        with pytest.raises(ValueError, match="must be alphanumeric"):
            _ = rec.subject


class TestEEGDatasetCrawler:
    @pytest.mark.parametrize(
        "cond, path_template",
        [
            (None, "sub-01/sub-01.eeg"),
            ("rest", "sub-01/rest/sub-01.eeg"),
            ("video", "sub-01/video/sub-01.eeg"),
        ],
    )
    def test_correct_nesting(self, fs, cond, path_template):
        full_path = Path("/data") / path_template
        fs.create_file(full_path)

        config = {
            "root_path": "/data",
            "expected_participants": ["sub-01"],
            "expected_conditions": [cond] if cond else None,
            "extension": ".eeg",
        }

        model = EEGDatasetCrawler(**config)

        res = model.found_recordings
        assert len(res) == 1
        assert res[0].condition == cond
        assert str(res[0].path) == str(full_path)

    @pytest.mark.parametrize(
        "cond, path_template",
        [
            ("rest", "sub-01/sub-01.eeg"),
            ("rest", "rest/sub-01/sub-01.eeg"),
        ],
    )
    def test_incorrect_nesting(self, fs, cond, path_template):
        full_path = Path("/data") / path_template
        fs.create_file(full_path)

        config = {
            "root_path": "/data",
            "expected_participants": ["sub-01"],
            "expected_conditions": [cond] if cond else None,
            "extension": ".eeg",
        }

        with pytest.raises(ValidationError):
            EEGDatasetCrawler(**config)

    def test_multiple_conditions(self, fs):
        root = "/data"
        p_id = "sub-01"
        conditions = ["rest", "video"]

        for cond in conditions:
            fs.create_file(Path(root) / p_id / cond / f"{p_id}.eeg")

        config = {
            "root_path": root,
            "expected_participants": [p_id],
            "expected_conditions": conditions,
            "extension": ".eeg",
        }

        model = EEGDatasetCrawler(**config)

        assert len(model.found_recordings) == 2
        assert model.found_recordings[0].condition == "rest"
        assert model.found_recordings[1].condition == "video"

    @pytest.mark.parametrize("file_list", [(["sub-01.eeg"]), (["sub-01.eeg", "readme.txt"])])
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
        "file_list, error_msg",
        [
            (["sub-01.txt"], "No .eeg file found"),
            (["sub-01.eeg", "readme.eeg"], "Multiple EEG files found"),
        ],
    )
    def test_invalid_single_leaf_rule(self, fs, file_list, error_msg):
        for file in file_list:
            fs.create_file(Path("/data/sub-01") / file)

        config = {
            "root_path": "/data",
            "expected_participants": ["sub-01"],
            "extension": ".eeg",
        }

        with pytest.raises(ValidationError) as excinfo:
            EEGDatasetCrawler(**config)

        assert error_msg in str(excinfo.value)

    def test_expected_participants(self, fs):
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

        missing_dir = config["expected_participants"][0]

        with pytest.raises(ValidationError) as excinfo:
            EEGDatasetCrawler(**config)

        assert f"Expected participant directory missing: {missing_dir}" in str(excinfo.value)

    def test_no_participants(self, fs):
        config = {
            "root_path": "/data",
            "expected_participants": [],
            "extension": ".eeg",
        }

        fs.create_dir(config["root_path"])

        with pytest.raises(ValidationError) as excinfo:
            EEGDatasetCrawler(**config)

        assert "too_short" in str(excinfo.value)

    @pytest.mark.parametrize(
        "existing_path, cond, expected_missing",
        [
            ("sub-01", "rest", "rest"),
            ("sub-01/video/", "video/ses-01", "ses-01"),
            ("sub-01/", "video/ses-01", "video/ses-01"),
        ],
    )
    def test_recursive_error_reporting(self, fs, existing_path, cond, expected_missing):
        root = "/data"
        p_id = "sub-01"

        expected_found = Path(root) / existing_path
        fs.create_dir(expected_found)

        config = {
            "root_path": root,
            "expected_participants": [p_id],
            "expected_conditions": [cond],
            "extension": ".eeg",
        }

        with pytest.raises(ValidationError) as excinfo:
            EEGDatasetCrawler(**config)

        error_str = str(excinfo.value)
        assert f"Structure broken for {p_id}" in error_str
        assert f"Found {expected_found}" in error_str
        assert f"expected to find {Path(expected_missing)}" in error_str

    @pytest.mark.parametrize(
        "root_path, expected_error",
        [
            ("/non_existent", "path_not_directory"),
            (None, "Field required"),
        ],
    )
    def test_root_path_not_present(self, root_path, expected_error):

        config = {
            "expected_participants": ["sub-01"],
            "extension": ".eeg",
        }
        if root_path is not None:
            config["root_path"] = root_path

        with pytest.raises(ValidationError) as excinfo:
            EEGDatasetCrawler(**config)

        assert expected_error in str(excinfo.value)

    def test_root_path_is_file(self, fs):

        config = {
            "root_path": "/test.txt",
            "expected_participants": ["sub-01"],
            "extension": ".eeg",
        }

        fs.create_file(config["root_path"])

        with pytest.raises(ValidationError) as excinfo:
            EEGDatasetCrawler(**config)

        assert "path_not_directory" in str(excinfo.value)
