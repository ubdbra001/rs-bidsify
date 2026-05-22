import logging
from datetime import datetime
from pathlib import Path

import colorlog


def setup_file_handler(log_dir: Path, logger: logging.Logger, level: str | int = logging.INFO):
    """
    Configure and attach a timestamped file handler to a logger.

    Creates a log directory if it does not exist and initializes a file
    handler with a standardized formatting string. The log file is
    automatically named using the current system timestamp in
    'log_YYYYMMDD_HHMMSS.log' format.

    Parameters
    ----------
    log_dir : Path
        The directory path where log files should be stored.
    logger : logging.Logger
        The logger instance to which the file handler will be added.
    level : str or int, optional
        The logging level for the file handler. By default logging.INFO.

    Returns
    -------
    None
        This function modifies the `logger` object in-place.

    Notes
    -----
    The log format used is:
    '%(asctime)s | %(levelname)-8s | [%(name)s:%(lineno)d] | %(message)s'
    """
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
    """
    Configure and attach a colorized console stream handler to a logger.

    Utilizes the `colorlog` library to provide visually distinguished log
    levels in the terminal. The handler is initialized with a standardized
    format string including timestamps and source line numbers.

    Parameters
    ----------
    logger : logging.Logger
        The logger instance to which the stream handler will be added.
    level : str or int, optional
        The logging level for the stream handler. By default logging.INFO.

    Returns
    -------
    None
        This function modifies the `logger` object in-place.

    Notes
    -----
    This function requires the `colorlog` package. The console output
    uses the following format:
    '%(asctime)s | %(log_color)s%(levelname)-8s%(reset)s | [%(name)s:%(lineno)d] | %(message)s'
    """
    stream_formatter = colorlog.ColoredFormatter(
        "%(asctime)s | %(log_color)s%(levelname)-8s%(reset)s | [%(name)s:%(lineno)d] | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    stream_handler = colorlog.StreamHandler()
    stream_handler.setFormatter(stream_formatter)
    stream_handler.setLevel(level)
    logger.addHandler(stream_handler)


def adjust_mne_logger(level: str | int = logging.INFO):
    """
    Redirect MNE-Python logging to the root logger.

    Clears any existing handlers assigned to the 'mne' logger and enables
    propagation. This ensures that MNE log messages are handled by the
    root logger's configurations (e.g., custom formatters or file handlers)
    rather than MNE's default internal logging.

    Parameters
    ----------
    level : str or int, optional
        The logging level to set for the MNE logger. By default logging.INFO.

    Returns
    -------
    None
        This function modifies the 'mne' logger instance in-place.
    """
    mne_logger = logging.getLogger("mne")
    mne_logger.handlers = []
    mne_logger.propagate = True
    mne_logger.setLevel(level)


def setup_logging(root_path: Path, level: str | int = logging.INFO):
    """
    Initialize and configure the root logger with file and stream handlers.

    This high-level utility synchronizes MNE logging, sets the global
    logging level, redirects Python warnings to the logging system,
    and attaches both a timestamped file handler and a colorized
    console handler.

    Parameters
    ----------
    root_path : Path
        The base directory where the 'logs' subdirectory will be created.
    level : str or int, optional
        The logging level to apply globally across all configured
        handlers. By default logging.INFO.

    Returns
    -------
    None
        Configures the global logging environment in-place.
    """
    adjust_mne_logger(level)

    logger = logging.getLogger()
    logger.setLevel(level)

    logging.captureWarnings(True)

    setup_file_handler(root_path, logger, level)
    setup_stream_handler(logger, level)
