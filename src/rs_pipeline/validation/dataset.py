from pathlib import Path
from pydantic import BaseModel, Field, model_validator, FilePath, DirectoryPath


class RecordingMetadata(BaseModel):
    participant: str
    condition: str | None
    session: str | None
    path: FilePath


class EEGDatasetCrawler(BaseModel):
    root_path: DirectoryPath
    expected_participants: list[str] = Field(min_length=1)
    expected_conditions: list[str] | None = Field(default=None, min_length=1)
    expected_sessions: list[str] | None = Field(default=None, min_length=1)
    extension: str

    found_recordings: list[RecordingMetadata] = Field(default_factory=list, exclude=True)

    @model_validator(mode="after")
    def verify_structure(self) -> "EEGDatasetCrawler":
        conditions = self.expected_conditions or [None]
        sessions = self.expected_sessions or [None]

        for p_id in self.expected_participants:
            p_path = self.root_path / p_id
            if not p_path.is_dir():
                raise ValueError(f"Expected participant directory missing: {p_id}")

            for cond in conditions:
                for sess in sessions:
                    current_path = p_path

                    if cond:
                        current_path /= cond

                    if sess:
                        current_path /= sess

                    eeg_file = self._check_leaf_node(current_path, p_id)

                    self.found_recordings.append(
                        RecordingMetadata(
                            participant=p_id,
                            condition=cond,
                            session=sess,
                            path=eeg_file,
                        )
                    )

        return self

    def _check_leaf_node(self, path: Path, p_id: str) -> Path:
        if not path.exists():
            current = path
            while not current.exists() and current != self.root_path:
                last_missing = current.name
                current = current.parent

            raise ValueError(
                f"Structure broken for {p_id}."
                f"Found {current}, but expected to find {last_missing} within"
            )

            # Look for EEG files
        eeg_files = list(path.glob(f"*{self.extension}"))

        if len(eeg_files) == 0:
            raise ValueError(f"No {self.extension} file found in {path}")
        if len(eeg_files) > 1:
            raise ValueError(f"Multiple EEG files found in {path} (Expected only one).")

        return eeg_files[0]
