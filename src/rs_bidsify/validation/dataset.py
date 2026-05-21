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
    """
    Metadata representation of a single EEG recording file.

    This model stores the relationship between a physical file on disk,
     its associated participant identifier, and the experimental condition.
    It includes logic to normalize participant IDs into BIDS-compliant
    subject strings.

    Attributes
    ----------
    participant : str
        The raw participant identifier (e.g., 'sub-001' or 'pilot_01').
    condition : str | None
        The experimental task or condition (e.g., 'resting', 'task-face').
    path : FilePath
        The validated system path to the raw EEG recording file.
    """

    participant: str
    condition: str | None
    path: FilePath

    @computed_field
    @property
    def subject(self) -> str:
        """
        Extract a BIDS-compliant subject ID from the participant string.

        Attempts to find an alphanumeric string following a dash or
        underscore. If no delimiter is found, it validates that the
        entire string is alphanumeric before returning it.

        Returns
        -------
        str
            The cleaned subject identifier.

        Raises
        ------
        ValueError
            If no delimiter is present and the participant ID contains
            non-alphanumeric characters.
        """
        result = re.findall("(?<=[-_])[a-zA-Z0-9]+$", self.participant)
        if result:
            return result[0]

        if not self.participant.isalnum():
            raise ValueError(f"Participant ID must be alphanumeric: {self.participant}")

        return self.participant


class EEGDatasetCrawler(BaseModel):
    """
    Crawler to validate and map the raw EEG dataset directory structure.

    Iterates through the root directory based on a list of expected
    participants and conditions. It verifies that the required folder
    hierarchy exists and contains exactly one EEG file per leaf node.

    Attributes
    ----------
    root_path : DirectoryPath
        The base directory where raw data is stored.
    expected_participants : list[str]
        A list of participant IDs that must have corresponding directories.
    expected_conditions : list[str] | None
        Optional list of task/condition subdirectories expected within
        each participant folder.
    extension : str
        The file extension of the raw EEG recordings (e.g., '.edf', '.mff').
    found_recordings : list[RecordingMetadata]
        A list of validated recording objects populated during the crawl.
        Excluded from model serialization.
    """

    root_path: DirectoryPath
    expected_participants: list[str] = Field(min_length=1)
    expected_conditions: list[str] | None = Field(default=None, min_length=1)
    extension: str

    found_recordings: list[RecordingMetadata] = Field(
        default_factory=list, exclude=True
    )

    @model_validator(mode="after")
    def verify_structure(self) -> "EEGDatasetCrawler":
        """
        Validate the dataset structure and populate found_recordings.

        Runs automatically after model initialization. It traverses the
        directory tree, checking for the existence of participant and
        condition folders, and delegates file checking to `_check_leaf_node`.

        Returns
        -------
        EEGDatasetCrawler
            The validated crawler instance with populated recording metadata.

        Raises
        ------
        ValueError
            If a participant directory is missing or if the structure
            validation fails at the leaf node.
        """
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
        """
        Verify the contents of a specific directory for EEG data.

        Checks that the directory exists and contains exactly one file
        matching the specified extension.

        Parameters
        ----------
        path : Path
            The directory path to inspect.
        p_id : str
            The participant ID currently being processed (for error reporting).

        Returns
        -------
        Path
            The path to the found EEG recording file.

        Raises
        ------
        ValueError
            If the path does not exist, if no EEG files are found, or if
            multiple EEG files are present.
        """
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
