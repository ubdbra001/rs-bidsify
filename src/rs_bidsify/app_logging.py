import logging
import colorlog
from datetime import datetime
from pathlib import Path


def setup_file_handler(
    log_dir: Path, logger: logging.Logger, level: str | int = "INFO"
):
    """Setup file logging"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"log_{timestamp}.log"

    log_dir.mkdir(parents=True, exist_ok=True)

    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | [%(name)s:%(lineno)d] | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(log_dir / log_filename)
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)

    logger.addHandler(file_handler)


def setup_stream_handler(logger: logging.Logger, level: str | int = logging.INFO):
    """Setup coluored console logging"""

    stream_formatter = colorlog.ColoredFormatter(
        "%(asctime)s | %(log_color)s%(levelname)-8s%(reset)s | [%(name)s:%(lineno)d] | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    stream_handler = colorlog.StreamHandler()
    stream_handler.setFormatter(stream_formatter)
    stream_handler.setLevel(level)
    logger.addHandler(stream_handler)


def adjust_mne_logger(level):
    """Make MNE log to the root logger"""
    mne_logger = logging.getLogger("mne")
    mne_logger.handlers = []
    mne_logger.propagate = True
    mne_logger.setLevel(level)


def setup_logging(root_path: Path, level: str | int = logging.INFO):
    """High level function to setup root logger"""

    adjust_mne_logger(level)

    logger = logging.getLogger()
    logger.setLevel(level)

    logging.captureWarnings(True)

    setup_file_handler(root_path, logger, level)
    setup_stream_handler(logger, level)
