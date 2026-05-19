import logging
import pytest
from pydantic import BaseModel
from unittest.mock import MagicMock
from rs_bidsify import enrichment
from rs_bidsify.validation.description import (
    AcquisitionSpecs,
    EEGChanSpec,
    DatasetMetadata,
    ExtraSpec,
    AcceptableImpedance,
    )
from rs_bidsify.validation.subject import SubjectMetadata

@pytest.fixture
def mock_raw():
    raw = MagicMock()
    raw.info = {}
    raw.ch_names = ["EEG1", "AUX1", "AUX2"]
    raw.annotations = MagicMock()
    raw.annotations.description = ["Event1", "Event2"]
    return raw

class TestMNEEnrichment:
    """Test the functions that update the MNE BaseRaw object (pre-write)"""

    def test_set_line_frequency(self, mock_raw):
        spec = MagicMock(spec=AcquisitionSpecs)
        spec.power_line_freq = 50
        
        enrichment.set_line_frequency(mock_raw, spec)
        
        assert mock_raw.info["line_freq"] == 50

    @pytest.mark.parametrize(
            "initial_info, expected_result",
            [
                (None, {"age": 30}),
                ({"hand": 1}, {"age": 30, "hand": 1}),
            ]
    )
    def test_set_subject_info(self, mock_raw, initial_info, expected_result):
        mock_raw.info = {"subject_info": initial_info}
        subj_metadata = MagicMock(spec=SubjectMetadata)

        subj_metadata.subject_info_dump.return_value = {"age": 30}

        enrichment.set_subject_info(mock_raw, subj_metadata)

        assert mock_raw.info["subject_info"] == expected_result

    def test_set_electrode_montage(self, mock_raw):
        pass

class MockModel(BaseModel):
    field_a: str | None = None
    field_b: int | None = None
    field_c: str = "ignore"

class TestBIDSEnrichment:
    """Test the functions that update the BIDS files (post-write)"""

    @pytest.mark.parametrize(
            "target_function, model, input_data, base_entries, expected_entries",
            [
                pytest.param(
                    enrichment.set_reference_chan,
                    EEGChanSpec,
                    {"reference": "Cpz"},
                    {},
                    {"EEGReference": "Cpz"},
                    id="Ref-channel"
                ),
                pytest.param(
                    enrichment.set_ground_chan,
                    EEGChanSpec,
                    {"ground": "Linked Mastoids"},
                    {},
                    {"EEGGround": "Linked Mastoids"},
                    id="Ground-channel"
                ),
                pytest.param(
                    enrichment.set_device_info,
                    AcquisitionSpecs,
                    {"amplifier_model": "BrainAmp", "software": "v1.2"},
                    {},
                    {"ManufacturersModelName": "BrainAmp", "SoftwareVersions": "v1.2"},
                    id="Device-info"
                ),
                pytest.param(
                    enrichment.set_institution_info,
                    DatasetMetadata,
                    {"institution_name": "University of Sheffield", "institution_dept": "Computer Science"},
                    {},
                    {"InstitutionName": "University of Sheffield", "InstitutionalDepartmentName": "Computer Science"},
                    id="Institution-info"
                ),
                pytest.param(
                    enrichment.set_extras,
                    ExtraSpec,
                    {
                        "faraday_cage": True,
                        "conductive_medium": "Gel",
                        "acceptable_impedance": AcceptableImpedance(value=100, units="ohms")
                    },
                    {},
                    {
                        "FaradayCage": True,
                        "ConductiveMedium": "Gel",
                        "AcceptableImpedence": {"value": 100, "units": "ohms"}
                    },
                    id="Extra-info"
                ),
                pytest.param(
                    enrichment.set_device_info,
                    AcquisitionSpecs,
                    {"amplifier_model": "BrainAmp"},
                    {"TaskName": "MemoryTask"},
                    {"ManufacturersModelName": "BrainAmp", "TaskName": "MemoryTask"},
                    id="update-unrelated-data"
                ),
                pytest.param(
                    enrichment.set_institution_info,
                    DatasetMetadata,
                    {"institution_name": "Uni of Sheffield"},
                    {"InstitutionName": "Old Name"},
                    {"InstitutionName": "Uni of Sheffield"},
                    id="update-existing-data"
                )
            ]
    )
    def test_enrichment_mappings(self, target_function, model, input_data, base_entries, expected_entries):
        entries = base_entries

        model_spec = model.model_construct(**input_data)

        target_function(entries, model_spec)

        for key, exp_val in expected_entries.items():
            assert entries.get(key) == exp_val

    def test_map_spec_to_bids(self, caplog):
        caplog.set_level(logging.INFO)

        source = MockModel(field_a="hello", field_b=None)

        mapping = {
            "BIDS_A": "field_a", 
            "BIDS_B": "field_b",
            "BIDS_C": "field_c"
        }

        updates = {"Existing": "Data"} # Ensure we don't wipe existing dicts

        enrichment.map_spec_to_bids(source, mapping, updates)

        assert updates["BIDS_A"] == "hello"
        assert "BIDS_B" not in updates
        assert updates["BIDS_C"] == "ignore"
        assert updates["Existing"] == "Data"

        assert "Queued update - BIDS_A: hello" in caplog.text
        assert "BIDS_B" not in caplog.text # Should not log for None values


class TestEnrichmentOrchestration:
    def test_enrich_eeg_sidecar_orchestration(self, mocker):

        mock_io = mocker.patch("rs_bidsify.io.write_enriched_sidecar")
        
        funcs = [
            "set_reference_chan", "set_ground_chan", "set_hardware_filters",
            "set_software_filters", "set_device_info", "set_institution_info", "set_extras"
        ]
        mocks = {name: mocker.patch(f"rs_bidsify.enrichment.{name}") for name in funcs}

        mock_spec = MagicMock()
        mock_spec.acquisition_spec.extras = MagicMock()

        enrichment.enrich_eeg_sidecar(MagicMock(), mock_spec)

        for name, m in mocks.items():
            assert m.called, f"{name} was never called!"
        
        mock_io.assert_called_once()

    @pytest.mark.parametrize(
            "extras_val, add_extras_flag, expected_call_count",
            [
                pytest.param(MagicMock(), True, 1, id="Data-Exists-Flag-On-Calls"),
                pytest.param(MagicMock(), False, 0, id="Data-Exists-Flag-Off-Skips"),
                pytest.param(None, True, 0, id="Data-None-Flag-On-Skips"),
                pytest.param(None, False, 0, id="Data-None-Flag-Off-Skips"),
            ]
    )
    def test_enrich_eeg_sidecar_add_extras_flag(self, mocker, extras_val, add_extras_flag, expected_call_count):

        mocker.patch("rs_bidsify.io.write_enriched_sidecar")
        mock_set_extras = mocker.patch("rs_bidsify.enrichment.set_extras")

        funcs = [
            "set_reference_chan", "set_ground_chan", "set_hardware_filters",
            "set_software_filters", "set_device_info", "set_institution_info"
        ]
        [mocker.patch(f"rs_bidsify.enrichment.{name}") for name in funcs]

        mock_spec = MagicMock()
        mock_spec.acquisition_spec.extras = extras_val


        enrichment.enrich_eeg_sidecar(
            MagicMock(), mock_spec, add_extras=add_extras_flag
        )

        assert mock_set_extras.call_count == expected_call_count

    def test_enrich_mne_object_orchestration(self, mocker):
        mock_eeg_data = mocker.MagicMock() 
        mock_spec = mocker.MagicMock()

        targets = {
            "set_line_frequency": mock_spec.acquisition_spec,
            "set_aux_channel_types": mock_spec.acquisition_spec.aux_channels,
            "set_electrode_montage": mock_spec.acquisition_spec.eeg_channels,
            "set_events": mock_spec.resting_state.events,
        }

        mocks = {name: mocker.patch(f"rs_bidsify.enrichment.{name}") for name in targets}

        enrichment.enrich_mne_object(mock_eeg_data, mock_spec)

        for name, mock_func in mocks.items():
                mock_func.assert_called_once_with(mock_eeg_data, targets[name])