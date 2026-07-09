import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytest
import tomlkit
import yaml
from mne_bids import BIDSPath

from rs_bidsify import io
from rs_bidsify.validation.dataset import RecordingMetadata
from rs_bidsify.validation.description import DescriptionSpec


class TestRollbackRecording:
    def test_only_rollback_specific_condition(self, fs):
        sub_dir = Path("/mock_bids/sub-01")

        fs.create_dir(sub_dir)
        fs.create_file(sub_dir / "sub-01_task-rest_eeg.vhdr")
        fs.create_file(sub_dir / "sub-01_task-rest_eeg.json")

        safe_file = sub_dir / "sub-01_task-face_eeg.json"
        fs.create_file(safe_file)

        recording = RecordingMetadata.model_construct(
            condition="rest",
            participant="sub-01",
        )

        io.rollback_recording_files(sub_dir, recording)

        assert not (sub_dir / "sub-01_task-rest_eeg.vhdr").exists()
        assert not (sub_dir / "sub-01_task-rest_eeg.json").exists()
        assert safe_file.exists()
        assert sub_dir.exists()

    def test_rollback_when_no_sidecars_remain(self, fs):
        sub_dir = Path("/mock_bids/sub-01")

        fs.create_dir(sub_dir)
        fs.create_file(sub_dir / "sub-01_task-rest_eeg.vhdr")
        fs.create_file(sub_dir / "sub-01_task-rest_eeg.json")

        recording = RecordingMetadata.model_construct(
            condition="rest",
            participant="sub-01",
        )

        io.rollback_recording_files(sub_dir, recording)

        assert not sub_dir.exists()

    def test_rollback_when_no_condition(self, fs):
        sub_dir = Path("/mock_bids/sub-01")

        fs.create_dir(sub_dir)
        fs.create_file(sub_dir / "sub-01_task-rest_eeg.vhdr")
        fs.create_file(sub_dir / "sub-01_task-rest_eeg.json")

        safe_file = sub_dir / "sub-01_task-face_eeg.json"
        fs.create_file(safe_file)

        recording = RecordingMetadata.model_construct(participant="sub-01", condition=None)

        io.rollback_recording_files(sub_dir, recording)

        assert not sub_dir.exists()

    def test_no_rollback_missing_directory(self):
        sub_dir = Path("/mock_bids/sub-missing")

        recording = RecordingMetadata.model_construct(
            condition="rest",
            participant="sub-01",
        )

        # Should execute safely without throwing errors on a non-existent path
        io.rollback_recording_files(sub_dir, recording)
        assert not sub_dir.exists()

    def test_rollback_error_handling(self, fs, mocker, caplog):
        sub_dir = Path("/mock_bids/sub-01")
        fs.create_dir(sub_dir)

        recording = RecordingMetadata.model_construct(
            condition="rest",
            participant="sub-01",
        )

        # Force a crash on rmtree to simulate a OS permissions gridlock
        mocker.patch("shutil.rmtree", side_effect=PermissionError("Mocked access denied"))

        with caplog.at_level(logging.ERROR):
            io.rollback_recording_files(sub_dir, recording)

        assert "Clean up failed" in caplog.text
        assert "Mocked access denied" in caplog.text


class TestReadEEGRecording:
    def test_read_eeg_recording(self, mocker):
        fake_path = Path("path/to/recording.edf")

        mock_utc_now = datetime(2026, 6, 9, 14, 30, 00, tzinfo=UTC)

        mocker.patch("rs_bidsify.io.get_utc_today", return_value=mock_utc_now)

        mock_raw_instance = mocker.MagicMock()

        mock_read_raw = mocker.patch("rs_bidsify.io.read_raw", return_value=mock_raw_instance)

        result = io.read_eeg_recording(fake_path)

        mock_read_raw.assert_called_once_with(fake_path)

        mock_raw_instance.set_meas_date.assert_called_once_with(mock_utc_now)

        assert result == mock_raw_instance


class TestWriteEnrichedSidecar:
    def test_write_enriched_sidecar(self, fs):
        bids_root = Path("/mock_bids")
        subject = "01"
        task = "rest"

        target_dir = bids_root / f"sub-{subject}" / "eeg"
        fs.create_dir(target_dir)

        target_file = target_dir / f"sub-{subject}_task-{task}_eeg.json"
        initial_data = {"TaskName": "rest", "SamplingFrequency": 250}
        fs.create_file(target_file, contents=json.dumps(initial_data))

        bids_path = BIDSPath(
            subject=subject, task=task, datatype="eeg", suffix="eeg", extension=".vhdr", root=bids_root
        )

        updates = {"SamplingFrequency": 500, "PowerLineFrequency": 50}

        io.write_enriched_sidecar(bids_path, updates)

        updated_content = json.loads(target_file.read_text())

        assert updated_content["TaskName"] == "rest"

        assert updated_content["SamplingFrequency"] == 500

        assert updated_content["PowerLineFrequency"] == 50


class TestReadDescriptionFile:
    @pytest.mark.parametrize(
        ("input_file", "write_function"),
        [
            ("dataset_description.json", json.dumps),
            ("dataset_description.yaml", yaml.dump),
            ("dataset_description.toml", tomlkit.dumps),
        ],
    )
    def test_read_description_file_load_success(self, fs, mocker, input_file, write_function):
        file_path = Path("/mock") / input_file
        raw_file_content = {"Name": "Test Dataset", "BIDSVersion": "1.8.0"}

        fs.create_file(file_path, contents=write_function(raw_file_content))

        mock_validated_model = mocker.MagicMock(spec=DescriptionSpec)
        mock_validate = mocker.patch("rs_bidsify.io.DescriptionSpec.model_validate", return_value=mock_validated_model)

        result = io.read_description_file(file_path)

        mock_validate.assert_called_once_with(raw_file_content)
        assert result == mock_validated_model


class TestReadBidsTsv:
    def test_read_bids_tsv_success(self, fs):
        tsv_path = Path("/mock_bids/participants.tsv")

        raw_tsv = "participant_id\tage\tsex\tgroup\nsub-01\t22\tM\tcontrol\nsub-02\t30\tF\tpatient\n"

        fs.create_file(tsv_path, contents=raw_tsv)

        df = io.read_bids_tsv(tsv_path)

        assert isinstance(df, pd.DataFrame)

        assert df.index.name == "participant_id"
        assert list(df.index) == ["sub-01", "sub-02"]

        assert list(df.columns) == ["age", "sex", "group"]

        assert df.loc["sub-01", "age"] == 22
        assert df.loc["sub-02", "group"] == "patient"

    def test_read_bids_tsv_single_column_file_raises_error(self, fs):
        tsv_path = Path("/mock_bids/just_ids.tsv")

        # This file has tabs, but literally only contains one column of information
        single_col_content = "participant_id\nsub-01\nsub-02\n"
        fs.create_file(tsv_path, contents=single_col_content)

        with pytest.raises(ValueError, match="contains no data columns after parsing"):
            io.read_bids_tsv(tsv_path)


class TestWriteBidsTsv:
    def test_write_bids_tsv_success(self, fs):
        out_path = Path("/mock_bids/participans.tsv")

        fs.create_dir(out_path.parent)

        df = pd.DataFrame(
            {"age": [25, 34], "sex": ["M", "F"]}, index=pd.Index(["sub-01", "sub-02"], name="participant_id")
        )

        io.write_bids_tsv(out_path, df)

        assert out_path.exists()

        result = pd.read_csv(out_path, sep="\t", index_col=0)

        assert result.shape == (2, 2)
        assert result.index.name == "participant_id"
        assert list(result.index) == ["sub-01", "sub-02"]
        assert list(result.columns) == ["age", "sex"]
        assert result.loc["sub-01", "age"] == 25
        assert result.loc["sub-02", "sex"] == "F"


class TestCheckTaskExists:
    @pytest.mark.parametrize(
        "task_name, exp_result", [pytest.param("rest", True, id="match"), pytest.param("video", False, id="no match")]
    )
    def test_check_task_exists(self, fs, task_name, exp_result):
        sub_dir = Path("/mock_bids/sub-001")

        nested_eeg_dir = sub_dir / "eeg"
        fs.create_dir(nested_eeg_dir)
        fs.create_file(nested_eeg_dir / "sub-001_task-rest_eeg.vhdr")

        assert io.check_task_exists(sub_dir, task_name) is exp_result

    def test_check_task_exists_missing_dir(self, fs):
        sub_dir = Path("/mock_bids/sub-missing")

        assert io.check_task_exists(sub_dir, "rest") is False


class TestReadDescriptionSpreadsheet:
    def test_read_description_spreadsheet(self, mocker):
        sheet_path = Path("/mock_bids/metadata.ods")

        sheet_info = {
            "participants": {"sheet_name": "Demographics", "usecols": ["participant_id", "age"]},
            "codebook": {"sheet_name": "Data Dictionary"},
        }

        mock_df_participants = mocker.MagicMock(spec=pd.DataFrame)
        mock_df_codebook = mocker.MagicMock(spec=pd.DataFrame)

        def read_excel_side_effect(path, **kwargs):
            if kwargs.get("sheet_name") == "Demographics":
                return mock_df_participants
            if kwargs.get("sheet_name") == "Data Dictionary":
                return mock_df_codebook
            return None

        mock_read = mocker.patch("pandas.read_excel", side_effect=read_excel_side_effect)

        result = io.read_description_spreadsheet(sheet_path, sheet_info, sheet_type="participant")

        assert isinstance(result, dict)
        assert len(result) == 2

        assert result["participants"] == mock_df_participants
        assert result["codebook"] == mock_df_codebook

        mock_read.assert_any_call(sheet_path, sheet_name="Demographics", usecols=["participant_id", "age"])
        mock_read.assert_any_call(sheet_path, sheet_name="Data Dictionary")


class TestWritePhenotypeData:
    @pytest.fixture
    def sample_phenotype_data(self):
        dataset_df = pd.DataFrame(
            {"age": [20, 25, 45]}, index=pd.Index(["sub-01", "sub-02", "sub-03"], name="participant_id")
        )

        codebook_df = pd.DataFrame({"Description": ["Participant Age"]}, index=["age"])

        return {"dataset": dataset_df, "codebook": codebook_df}

    def test_write_phenotype_data_all_subjects(self, fs, sample_phenotype_data):
        root_path = Path("/mock_bids")
        fs.create_dir(root_path)

        missing_ids = []

        io.write_phenotype_data(sample_phenotype_data, root_path, missing_ids)

        target_dir = root_path / "phenotype"
        tsv_path = target_dir / "phenotype.tsv"
        json_path = target_dir / "phenotype.json"

        assert target_dir.exists()
        assert tsv_path.exists()
        assert json_path.exists()

        result_df = pd.read_csv(tsv_path, sep="\t", index_col=0)
        assert list(result_df.index) == ["sub-01", "sub-02", "sub-03"]
        assert result_df.loc["sub-03", "age"] == 45

        with open(json_path) as f:
            result_json = json.load(f)
        assert "age" in result_json
        assert result_json["age"]["Description"] == "Participant Age"

    def test_write_phenotype_data_with_filtering(self, fs, sample_phenotype_data):
        root_path = Path("/mock_bids")
        fs.create_dir(root_path)

        missing_ids = ["sub-03"]

        io.write_phenotype_data(sample_phenotype_data, root_path, missing_ids)

        target_dir = root_path / "phenotype"
        tsv_path = target_dir / "phenotype.tsv"

        result_df = pd.read_csv(tsv_path, sep="\t", index_col=0)

        assert list(result_df.index) == ["sub-01", "sub-02"]
        assert "sub-03" not in result_df.index


class TestCleanupParticipantsTsv:
    @pytest.mark.parametrize(
        "missing_ids, expected_remaining_ids",
        [
            pytest.param(["sub-03"], ["sub-01", "sub-02", "sub-04"], id="remove_single_subject"),
            pytest.param(
                ["sub-03", "sub-04"],
                [
                    "sub-01",
                    "sub-02",
                ],
                id="remove_multiple_subjects",
            ),
            pytest.param(
                ["sub-02", "sub-04"],
                [
                    "sub-01",
                    "sub-03",
                ],
                id="remove_multiple_noncontiguous_subjects",
            ),
            pytest.param(
                [],
                [
                    "sub-01",
                    "sub-02",
                    "sub-03",
                    "sub-04",
                ],
                id="remove_no_subjects",
            ),
        ],
    )
    def test_cleanup_participants_tsv_success(self, fs, missing_ids, expected_remaining_ids):
        """Test that the function successfully prunes target rows from a physical TSV file on disk."""
        out_path = Path("/mock_bids")
        tsv_path = out_path / "participants.tsv"

        raw_tsv = "participant_id\tage\tsex\nsub-01\t22\tM\nsub-02\t30\tF\nsub-03\t45\tM\nsub-04\t28\tF\n"
        fs.create_file(tsv_path, contents=raw_tsv)

        io.cleanup_participants_tsv(missing_ids=missing_ids, out_path=out_path)

        result_df = pd.read_csv(tsv_path, sep="\t", index_col=0)

        assert list(result_df.index) == expected_remaining_ids
        assert result_df.loc["sub-01", "age"] == 22
        assert result_df.loc["sub-01", "sex"] == "M"
