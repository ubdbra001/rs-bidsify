import logging
from pathlib import Path

import colorlog
import pytest

from rs_bidsify import app_logging


@pytest.fixture(autouse=True)
def cleanup_logging():
    yield
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)

    mne_logger = logging.getLogger("mne")
    mne_logger.handlers = []


class TestLoggingSetup:
    def test_file_handler_creates_directory_and_file(self, fs):
        log_dir = Path("/logs")
        logger = logging.getLogger("test_file_logger")

        app_logging.setup_file_handler(log_dir, logger)

        assert log_dir.exists()

        log_files = list(log_dir.glob("log_*.log"))
        assert len(log_files) == 1

        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)

    def test_adjust_mne_logger_resets_state(self):
        mne_logger = logging.getLogger("mne")
        mne_logger.addHandler(logging.StreamHandler())

        app_logging.adjust_mne_logger(logging.DEBUG)

        assert len(mne_logger.handlers) == 0
        assert mne_logger.propagate is True
        assert mne_logger.level == logging.DEBUG

    def test_setup_stream_handler_adds_colored_formatter(self):
        logger = logging.getLogger("test_stream_logger")
        app_logging.setup_stream_handler(logger)

        handler = next(
            h for h in logger.handlers if isinstance(h, colorlog.StreamHandler)
        )
        assert isinstance(handler.formatter, colorlog.ColoredFormatter)

    def test_setup_logging_configures_root(self, fs):
        log_path = Path("/data/logs")
        app_logging.setup_logging(log_path, level="DEBUG")

        root_logger = logging.getLogger()

        assert root_logger.level == logging.DEBUG
        assert len(root_logger.handlers) >= 2

        # Check if warnings are captured
        assert logging.captureWarnings(True) is None
