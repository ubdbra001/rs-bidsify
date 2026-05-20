import pytest

from pathlib import Path
from unittest.mock import MagicMock, patch

from rs_bidsify import discovery

class TestFindFile:

    def test_find_single_file(self, fs):

        expected_fpath = Path("/tmp") / "test.file"
        fs.create_file(expected_fpath)

        result = discovery.find_file(expected_fpath.parent, "file")

        assert expected_fpath == result

    def test_find_multiple_files(self, fs):
        files = ["test1.file", "test2.file"]

        root_path = Path("/tmp")

        [fs.create_file(root_path / file) for file in files]

        with pytest.raises(ValueError) as excinfo:
            discovery.find_file(root_path, "file")

        assert f"found {len(files)}" in str(excinfo.value)

    def test_find_no_files(self, fs):
        files = ["test1.file", "test2.file"]

        root_path = Path("/tmp")

        [fs.create_file(root_path / file) for file in files]

        with pytest.raises(ValueError) as excinfo:
            discovery.find_file(root_path, "eeg")

        assert f"found 0" in str(excinfo.value)

class TestDiscoveryMocks:
    @patch("rs_bidsify.discovery.find_file")
    @patch("rs_bidsify.io.read_description_json")
    def test_find_description_spec(self, mock_read, mock_find):
        mock_path = Path("/tmp/data.json")
        mock_find.return_value = mock_path
        
        discovery.find_description_spec(Path("/tmp"), "json")
        
        mock_find.assert_called_once_with(Path("/tmp"), "json")
        mock_read.assert_called_once_with(mock_path)

    @patch("rs_bidsify.discovery.find_file")
    @patch("rs_bidsify.io.read_description_spreadsheet")
    def test_find_dataset_spreadsheets_success(self, mock_read, mock_find):
        mock_find.return_value = Path("/tmp/data.ods")
        sheet_info = {"participant": {"cols": []}, "phenotype": {"cols": []}}
        mock_read.side_effect = [{"data": "p_val"}, {"data": "ph_val"}]
        
        p, ph = discovery.find_dataset_spreadsheets(Path("/tmp"), sheet_info)
        
        assert p == {"data": "p_val"}
        assert ph == {"data": "ph_val"}
        assert mock_read.call_count == 2

    @patch("rs_bidsify.discovery.find_file")
    @patch("rs_bidsify.io.read_description_spreadsheet")
    def test_find_dataset_spreadsheets_phenotype_failure(self, mock_read, mock_find):
        mock_find.return_value = Path("/tmp/data.ods")
        sheet_info = {"participant": {"cols": []}, "phenotype": {"cols": []}}
        mock_read.side_effect = [{"data": "p_val"}, Exception("Sheet missing")]
        
        p, ph = discovery.find_dataset_spreadsheets(Path("/tmp"), sheet_info)
        
        assert p == {"data": "p_val"}
        assert ph is None