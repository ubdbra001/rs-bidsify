import logging
import re
from pathlib import Path
from pydantic import (
    BaseModel,
    Field,
    model_validator,
    FilePath,
    DirectoryPath,
    computed_field,
)

logger = logging.getLogger(__name__)


class RecordingMetadata(BaseModel):
    participant: str
    condition: str | None
    path: FilePath

    @computed_field
    @property
    def subject(self) -> str:
        result = re.findall("(?<=[-_])[a-zA-Z0-9]+$", self.participant)
        if result:
            return result[0]
        
        if not self.participant.isalnum():
            raise ValueError(f"Participant ID must be alphanumeric: {self.participant}")
        
        return self.participant


class EEGDatasetCrawler(BaseModel):
    root_path: DirectoryPath
    expected_participants: list[str] = Field(min_length=1)
    expected_conditions: list[str] | None = Field(default=None, min_length=1)
    extension: str

    found_recordings: list[RecordingMetadata] = Field(
        default_factory=list, exclude=True
    )

    @model_validator(mode="after")
    def verify_structure(self) -> "EEGDatasetCrawler":
        conditions = self.expected_conditions or [None]

        logger.info(f"Crawling recordings in {self.root_path}")

        for p_id in self.expected_participants:
            p_path = self.root_path / p_id
            if not p_path.is_dir():
                raise ValueError(f"Expected participant directory missing: {p_id}")

            for cond in conditions:
                current_path = p_path

                if cond:
                    current_path /= cond

                eeg_file = self._check_leaf_node(current_path, p_id)

                self.found_recordings.append(
                    RecordingMetadata(
                        participant=p_id,
                        condition=cond,
                        path=eeg_file,
                    )
                )

        logger.info(
            f"Recording crawl complete, found {len(self.found_recordings)} valid recordings"
        )
        return self

    def _check_leaf_node(self, path: Path, p_id: str) -> Path:
        if not path.exists():
            current = path
            while not current.exists() and current != self.root_path:
                current = current.parent

            last_missing = path.relative_to(current)

            raise ValueError(
                f"Structure broken for {p_id}."
                f"Found {current}, but expected to find {last_missing} within"  # type: ignore
            )

            # Look for EEG files
        eeg_files = list(path.glob(f"*{self.extension}"))

        if len(eeg_files) == 0:
            raise ValueError(f"No {self.extension} file found in {path}")
        if len(eeg_files) > 1:
            raise ValueError(f"Multiple EEG files found in {path} (Expected only one).")

        return eeg_files[0]
