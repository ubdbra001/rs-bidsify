import json
import logging
import pytest

from datetime import datetime, timezone
from mne_bids import BIDSPath
from pathlib import Path


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
            condition="rest", participant="sub-01", 
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
            condition="rest", participant="sub-01", 
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

        recording = RecordingMetadata.model_construct(
            participant="sub-01", condition = None 
        )

        io.rollback_recording_files(sub_dir, recording)

        assert not sub_dir.exists()

    def test_no_rollback_missing_directory(self):
        sub_dir = Path("/mock_bids/sub-missing")
        
        recording = RecordingMetadata.model_construct(
            condition="rest", participant="sub-01", 
        )

        # Should execute safely without throwing errors on a non-existent path
        io.rollback_recording_files(sub_dir, recording)
        assert not sub_dir.exists()

    def test_rollback_error_handling(self, fs, mocker, caplog):
        sub_dir = Path("/mock_bids/sub-01")
        fs.create_dir(sub_dir)
        
        recording = RecordingMetadata.model_construct(
            condition="rest", participant="sub-01", 
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

        mock_utc_now = datetime(2026,6,9, 14, 30, 00, tzinfo=timezone.utc)

        mocker.patch(
            "rs_bidsify.io.get_utc_today", 
            return_value=mock_utc_now
        )

        mock_raw_instance = mocker.MagicMock()
    
        mock_read_raw = mocker.patch(
            "rs_bidsify.io.read_raw", 
            return_value=mock_raw_instance
        )

        result = io.read_eeg_recording(fake_path)

        mock_read_raw.assert_called_once_with(fake_path)
        
        mock_raw_instance.set_meas_date.assert_called_once_with(mock_utc_now)
    
        assert result == mock_raw_instance

    def test_read_eeg_recording_exception_propagation(self, mocker):
        fake_path = Path("/fake/corrupted_file.xyz")

        mocker.patch(
            "rs_bidsify.io.read_raw", 
            side_effect=ValueError("Unsupported file format")
        )

        # Verify that calling our function results in the exact same error
        with pytest.raises(ValueError, match="Unsupported file format"):
            io.read_eeg_recording(fake_path)

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
            subject=subject,
            task=task,
            datatype="eeg",
            suffix="eeg",
            extension=".vhdr",
            root=bids_root
        )

        updates = {"SamplingFrequency": 500, "PowerLineFrequency": 50}

        io.write_enriched_sidecar(bids_path, updates)

        updated_content = json.loads(target_file.read_text())

        assert updated_content["TaskName"] == "rest"
        
        assert updated_content["SamplingFrequency"] == 500
        
        assert updated_content["PowerLineFrequency"] == 50
    
    def test_write_enriched_sidecar_exception(self, mocker):
        bids_path = BIDSPath(subject="01", task="rest", root="/mock/bids")
        fake_updates = {"PowerLineFrequency": 50}

        mocker.patch(
            "rs_bidsify.io.update_sidecar_json",
            side_effect=RuntimeError("Simulated MNE-BIDS failure")
        )

        with pytest.raises(RuntimeError, match="Simulated MNE-BIDS failure"):
            io.write_enriched_sidecar(bids_path, fake_updates)

class TestReadDescriptionJson:
    def test_read_description_json_load_success(self, fs, mocker):
        json_path = Path("/mock/dataset_description.json")
        raw_json_content = '{"Name": "Test Dataset", "BIDSVersion": "1.8.0"}'
        
        fs.create_file(json_path, contents=raw_json_content)

        mock_validated_model = mocker.MagicMock(spec=DescriptionSpec)
        mock_validate = mocker.patch(
            "rs_bidsify.io.DescriptionSpec.model_validate_json",
            return_value=mock_validated_model
        )

        result = io.read_description_json(json_path)

        mock_validate.assert_called_once_with(raw_json_content)
        assert result == mock_validated_model

    def test_read_description_json_invalid_data(self, fs, mocker):
        json_path = Path("/mock/dataset_description.json")
        raw_json_content = '{"Name": "Test Dataset", "BIDSVersion": "1.8.0"}'
        
        fs.create_file(json_path, contents=raw_json_content)

        mocker.MagicMock(spec=DescriptionSpec)
        mock_validate = mocker.patch(
            "rs_bidsify.io.DescriptionSpec.model_validate_json",
            side_effect=ValueError()
        )

        with pytest.raises(ValueError):
            io.read_description_json(json_path)

        mock_validate.assert_called_once_with(raw_json_content)

    def test_read_description_json_missing_path(self, fs, mocker):
        json_path = Path("/mock/dataset_description.json")
        
        with pytest.raises(FileNotFoundError):
            io.read_description_json(json_path)

