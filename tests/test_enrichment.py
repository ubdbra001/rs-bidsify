import logging

import pytest
from pydantic import BaseModel

from rs_bidsify import enrichment
from rs_bidsify.validation.description import (
    AcceptableImpedance,
    AcquisitionSpecs,
    AuxChanSpec,
    DatasetMetadata,
    EEGChanSpec,
    ExtraSpec,
    FilterSpec,
    FilterTypeOptions,
    MNEChanTypes,
)
from rs_bidsify.validation.subject import SubjectMetadata


@pytest.fixture
def mock_raw(mocker):
    raw = mocker.MagicMock()
    raw.info = {}
    raw.ch_names = ["EEG1", "AUX1", "AUX2"]
    raw.annotations = mocker.MagicMock()
    raw.annotations.description = ["Event1", "Event2"]
    return raw


class TestMNEEnrichment:
    """Test the functions that update the MNE BaseRaw object (pre-write)"""

    def test_set_line_frequency(self, mocker, mock_raw):
        spec = mocker.MagicMock(spec=AcquisitionSpecs)
        spec.power_line_freq = 50

        enrichment.set_line_frequency(mock_raw, spec)

        assert mock_raw.info["line_freq"] == 50

    @pytest.mark.parametrize(
        "initial_info, expected_result",
        [
            (None, {"age": 30}),
            ({"hand": 1}, {"age": 30, "hand": 1}),
        ],
    )
    def test_set_subject_info(self, mocker, mock_raw, initial_info, expected_result):
        mock_raw.info = {"subject_info": initial_info}
        subj_metadata = mocker.MagicMock(spec=SubjectMetadata)

        subj_metadata.subject_info_dump.return_value = {"age": 30}

        enrichment.set_subject_info(mock_raw, subj_metadata)

        assert mock_raw.info["subject_info"] == expected_result

    @pytest.mark.parametrize(
        "mne_name, path, expected_source",
        [
            ("standard_1020", None, "standard_1020"),
            (None, "/path/to/custom_montage.lay", "/path/to/custom_montage.lay"),
        ],
    )
    def test_set_electrode_montage_success(
        self, mocker, mock_raw, caplog, mne_name, path, expected_source
    ):
        mock_spec = mocker.MagicMock()
        mock_dig_montage = mocker.MagicMock()

        mock_spec.montage.mne_name = mne_name
        mock_spec.montage.path = path
        mock_spec.montage.montage = mock_dig_montage

        with caplog.at_level(logging.INFO):
            enrichment.set_electrode_montage(mock_raw, mock_spec)

        mock_raw.set_montage.assert_called_once_with(mock_dig_montage)

        assert (
            f"Successfully applied montage from source: {expected_source}"
            in caplog.text
        )

    def test_set_aux_channel_types(self, mocker, mock_raw):
        real_spec = AuxChanSpec.model_construct(mne_type=MNEChanTypes.ECG)

        aux_chans = {"AUX1": real_spec}

        mocker.patch(
            "rs_bidsify.enrichment.check_mapping_alignment",
            return_value={"AUX1": "ecg"},
        )

        enrichment.set_aux_channel_types(mock_raw, aux_chans)

        mock_raw.set_channel_types.assert_called_once_with({"AUX1": "ecg"})

    def test_set_aux_channel_types_no_matches(self, mocker, mock_raw):

        fake_spec = AuxChanSpec.model_construct(
            mne_type=MNEChanTypes.EOG  # Use your actual Enum member here
        )

        mocker.patch("rs_bidsify.enrichment.check_mapping_alignment", return_value={})

        enrichment.set_aux_channel_types(mock_raw, {"AUX3": fake_spec})

        mock_raw.set_channel_types.assert_not_called()

    def test_set_events(self, mocker, mock_raw):
        event_info = {"Event1": "Stimulus"}

        mock_align = mocker.patch(
            "rs_bidsify.enrichment.check_mapping_alignment",
            return_value={"Event1": "Stimulus"},
        )

        enrichment.set_events(mock_raw, event_info)

        mock_align.assert_called_once_with(
            actual=mock_raw.annotations.description,
            expected=event_info,
            context="Events",
            strict_symmetry=True,
        )

        mock_raw.annotations.rename.assert_called_once_with({"Event1": "Stimulus"})

    def test_set_events_no_matches(self, mocker, mock_raw):
        event_info = {"Event3": "Missing"}

        mocker.patch("rs_bidsify.enrichment.check_mapping_alignment", return_value={})

        enrichment.set_events(mock_raw, event_info)

        mock_raw.annotations.rename.assert_not_called()


class MockModel(BaseModel):
    field_a: str | None = None
    field_b: int | None = None
    field_c: str = "ignore"


MOCK_FILTERS = [
    FilterSpec(
        name="HW1",
        type=FilterTypeOptions.HARDWARE,
        info={"cut-off frequency (Hz)": 260},
    ),
    FilterSpec(
        name="HW2",
        type=FilterTypeOptions.HARDWARE,
        info={"half-amplitude cutoff (Hz)": 500},
    ),
    FilterSpec(
        name="SW1", type=FilterTypeOptions.SOFTWARE, info={"Roll-off": "6dB/Octave"}
    ),
]


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
                id="Ref-channel",
            ),
            pytest.param(
                enrichment.set_ground_chan,
                EEGChanSpec,
                {"ground": "Linked Mastoids"},
                {},
                {"EEGGround": "Linked Mastoids"},
                id="Ground-channel",
            ),
            pytest.param(
                enrichment.set_device_info,
                AcquisitionSpecs,
                {"amplifier_model": "BrainAmp", "software": "v1.2"},
                {},
                {"ManufacturersModelName": "BrainAmp", "SoftwareVersions": "v1.2"},
                id="Device-info",
            ),
            pytest.param(
                enrichment.set_institution_info,
                DatasetMetadata,
                {
                    "institution_name": "University of Sheffield",
                    "institution_dept": "Computer Science",
                },
                {},
                {
                    "InstitutionName": "University of Sheffield",
                    "InstitutionalDepartmentName": "Computer Science",
                },
                id="Institution-info",
            ),
            pytest.param(
                enrichment.set_extras,
                ExtraSpec,
                {
                    "faraday_cage": True,
                    "conductive_medium": "Gel",
                    "acceptable_impedance": AcceptableImpedance(
                        value=100, units="ohms"
                    ),
                },
                {},
                {
                    "FaradayCage": True,
                    "ConductiveMedium": "Gel",
                    "AcceptableImpedence": {"value": 100, "units": "ohms"},
                },
                id="Extra-info",
            ),
            pytest.param(
                enrichment.set_device_info,
                AcquisitionSpecs,
                {"amplifier_model": "BrainAmp"},
                {"TaskName": "MemoryTask"},
                {"ManufacturersModelName": "BrainAmp", "TaskName": "MemoryTask"},
                id="update-unrelated-data",
            ),
            pytest.param(
                enrichment.set_institution_info,
                DatasetMetadata,
                {"institution_name": "Uni of Sheffield"},
                {"InstitutionName": "Old Name"},
                {"InstitutionName": "Uni of Sheffield"},
                id="update-existing-data",
            ),
        ],
    )
    def test_enrichment_mappings(
        self, target_function, model, input_data, base_entries, expected_entries
    ):
        entries = base_entries

        model_spec = model.model_construct(**input_data)

        target_function(entries, model_spec)

        for key, exp_val in expected_entries.items():
            assert entries.get(key) == exp_val

    def test_map_spec_to_bids(self, caplog):
        caplog.set_level(logging.INFO)

        source = MockModel(field_a="hello", field_b=None)

        mapping = {"BIDS_A": "field_a", "BIDS_B": "field_b", "BIDS_C": "field_c"}

        updates = {"Existing": "Data"}  # Ensure we don't wipe existing dicts

        enrichment.map_spec_to_bids(source, mapping, updates)

        assert updates["BIDS_A"] == "hello"
        assert "BIDS_B" not in updates
        assert updates["BIDS_C"] == "ignore"
        assert updates["Existing"] == "Data"

        assert "Queued update - BIDS_A: hello" in caplog.text
        assert "BIDS_B" not in caplog.text  # Should not log for None values

    def test_enrich_dataset_description(self, mocker):

        mock_maker = mocker.patch("rs_bidsify.enrichment.make_dataset_description")

        mock_path = mocker.MagicMock()
        mock_metadata = mocker.MagicMock(spec=DatasetMetadata)

        fake_dict = {"name": "Test Study", "authors": ["Researcher A"]}
        mock_metadata.create_dict.return_value = fake_dict

        enrichment.enrich_dataset_description(mock_metadata, mock_path)

        mock_metadata.create_dict.assert_called_once()

        mock_maker.assert_called_once_with(
            path=mock_path, name="Test Study", authors=["Researcher A"], overwrite=True
        )

    @pytest.mark.parametrize(
        "input_list, filter_type, expected",
        [
            (
                MOCK_FILTERS,
                FilterTypeOptions.HARDWARE,
                {
                    "HW1": {"cut-off frequency (Hz)": 260},
                    "HW2": {"half-amplitude cutoff (Hz)": 500},
                },
            ),
            (
                MOCK_FILTERS,
                FilterTypeOptions.SOFTWARE,
                {"SW1": {"Roll-off": "6dB/Octave"}},
            ),
            (MOCK_FILTERS, "Not specified", {}),
            ([], FilterTypeOptions.HARDWARE, {}),
        ],
    )
    def test_get_filters(self, input_list, filter_type, expected):
        res = enrichment.get_filters(input_list, filter_type)

        assert res == expected

    def test_set_hardware_filters(self, mocker):
        mock_get = mocker.patch("rs_bidsify.enrichment.get_filters")
        mock_set = mocker.patch("rs_bidsify.enrichment.set_filters")

        fake_filters = {"HW1": {"freq": 50}}
        mock_get.return_value = fake_filters

        entries = {}
        filters = [mocker.MagicMock(spec=FilterSpec)]

        enrichment.set_hardware_filters(entries, filters)

        mock_get.assert_called_once_with(filters, FilterTypeOptions.HARDWARE)
        mock_set.assert_called_once_with(entries, fake_filters, "HardwareFilters")

    def test_set_software_filters(self, mocker):
        mock_get = mocker.patch("rs_bidsify.enrichment.get_filters")
        mock_set = mocker.patch("rs_bidsify.enrichment.set_filters")

        fake_filters = {"SW1": {"freq": 0.5}}
        mock_get.return_value = fake_filters

        entries = {}
        filters = [mocker.MagicMock(spec=FilterSpec)]

        enrichment.set_software_filters(entries, filters)

        mock_get.assert_called_once_with(filters, FilterTypeOptions.SOFTWARE)
        mock_set.assert_called_once_with(entries, fake_filters, "SoftwareFilters")

    @pytest.mark.parametrize(
        "initial_entries, filter_dict, bids_key, expected_result",
        [
            pytest.param(
                {},
                {"HW1": {"cut-off frequency (Hz)": 260}},
                "HardwareFilters",
                {"HardwareFilters": {"HW1": {"cut-off frequency (Hz)": 260}}},
                id="succuss-update",
            ),
            pytest.param({}, {}, "HardwareFilters", {}, id="empty-filters"),
            pytest.param(
                {"SoftwareFilters": {"SW1": {}}},
                {"HW1": {"Roll-off": "6dB/Octave"}},
                "HardwareFilters",
                {
                    "SoftwareFilters": {"SW1": {}},
                    "HardwareFilters": {"HW1": {"Roll-off": "6dB/Octave"}},
                },
                id="preserve-existing",
            ),
        ],
    )
    def test_set_filters(self, initial_entries, filter_dict, bids_key, expected_result):
        enrichment.set_filters(initial_entries, filter_dict, bids_key)

        assert initial_entries == expected_result

    def test_set_filters_logging(self, caplog):
        entries = {}
        filter_dict = {"HW1": {}, "HW2": {}}

        with caplog.at_level("INFO"):
            enrichment.set_filters(entries, filter_dict, "HardwareFilters")

        assert "Queued update - HardwareFilters: HW1,HW2" in caplog.text


class TestEnrichmentOrchestration:
    def test_enrich_eeg_sidecar_orchestration(self, mocker):

        mock_io = mocker.patch("rs_bidsify.io.write_enriched_sidecar")

        funcs = [
            "set_reference_chan",
            "set_ground_chan",
            "set_hardware_filters",
            "set_software_filters",
            "set_device_info",
            "set_institution_info",
            "set_extras",
        ]
        mocks = {name: mocker.patch(f"rs_bidsify.enrichment.{name}") for name in funcs}

        mock_spec = mocker.MagicMock()
        mock_spec.acquisition_spec.extras = mocker.MagicMock()

        enrichment.enrich_eeg_sidecar(mocker.MagicMock(), mock_spec)

        for name, m in mocks.items():
            assert m.called, f"{name} was never called!"

        mock_io.assert_called_once()

    @pytest.mark.parametrize(
        "has_extras, add_extras_flag, expected_call_count",
        [
            pytest.param(True, True, 1, id="Data-Exists-Flag-On-Calls"),
            pytest.param(True, False, 0, id="Data-Exists-Flag-Off-Skips"),
            pytest.param(False, True, 0, id="Data-None-Flag-On-Skips"),
            pytest.param(False, False, 0, id="Data-None-Flag-Off-Skips"),
        ],
    )
    def test_enrich_eeg_sidecar_add_extras_flag(
        self, mocker, has_extras, add_extras_flag, expected_call_count
    ):

        mocker.patch("rs_bidsify.io.write_enriched_sidecar")
        mock_set_extras = mocker.patch("rs_bidsify.enrichment.set_extras")

        funcs = [
            "set_reference_chan",
            "set_ground_chan",
            "set_hardware_filters",
            "set_software_filters",
            "set_device_info",
            "set_institution_info",
        ]
        [mocker.patch(f"rs_bidsify.enrichment.{name}") for name in funcs]

        extras_val = mocker.MagicMock() if has_extras else None

        mock_spec = mocker.MagicMock()
        mock_spec.acquisition_spec.extras = extras_val

        enrichment.enrich_eeg_sidecar(
            mocker.MagicMock(), mock_spec, add_extras=add_extras_flag
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

        mocks = {
            name: mocker.patch(f"rs_bidsify.enrichment.{name}") for name in targets
        }

        enrichment.enrich_mne_object(mock_eeg_data, mock_spec)

        for name, mock_func in mocks.items():
            mock_func.assert_called_once_with(mock_eeg_data, targets[name])

    def test_enrich_channel_tsv_orchestration(self, mocker):
        mock_read = mocker.patch("rs_bidsify.io.read_bids_tsv")
        mock_write = mocker.patch("rs_bidsify.io.write_bids_tsv")
        mock_worker = mocker.patch("rs_bidsify.enrichment.set_channels_tsv")

        mock_path = mocker.MagicMock()
        mock_info = {"AUX1": mocker.MagicMock(spec=AuxChanSpec)}
        mock_existing_data = mocker.MagicMock()  # Representing the TSV content

        mock_read.return_value = mock_existing_data

        enrichment.enrich_channels_tsv_with_aux(mock_path, mock_info)

        mock_path.copy().update.assert_called_with(suffix="channels", extension="tsv")

        mock_worker.assert_called_once_with(mock_info, mock_existing_data)

        mock_write.assert_called_once_with(mocker.ANY, mock_existing_data)
