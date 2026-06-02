import logging
from datetime import datetime
from pathlib import Path

import colorlog


def setup_file_handler(log_dir: Path, logger: logging.Logger, level: str | int = logging.DEBUG):
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
    '%(log_color)s%(levelname)-8s%(reset)s | %(name)s | %(message)s'
    """
    stream_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-6s%(reset)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    stream_handler = colorlog.StreamHandler()
    stream_handler.setFormatter(stream_formatter)
    stream_handler.setLevel(level)

    stream_filter = DependencyFilter("rs_bidsify")
    stream_handler.addFilter(stream_filter)

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


def setup_logging(root_path: Path, level: str | int = logging.DEBUG):
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
        handlers. By default logging.DEBUG.

    Returns
    -------
    None
        Configures the global logging environment in-place.
    """
    adjust_mne_logger()

    logging.getLogger(name="filelock").setLevel(logging.INFO)

    logger = logging.getLogger()
    logger.setLevel(level)

    logging.captureWarnings(True)

    setup_file_handler(root_path, logger)
    setup_stream_handler(logger)


class DependencyFilter(logging.Filter):
    """
    A logging filter to restrict dependency logs while preserving errors.

    Allows all log records from the primary package namespace to pass through
    unfiltered. Records originating from third-party dependencies are dropped
    unless they meet or exceed the `logging.ERROR` threshold.

    Parameters
    ----------
    package_name : str
        The top-level name of your own application package (e.g., 'rs_bidsify').

    Attributes
    ----------
    package_name : str
        The root namespace string used to identify internal application logs.
    """

    def __init__(self, package_name: str) -> None:
        """Initialize the filter with the root application package name."""
        self.package_name = package_name

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Evaluate if a log record should be written or dropped.

        Parameters
        ----------
        record : logging.LogRecord
            The log record instance generated by the logging framework.

        Returns
        -------
        bool
            True if the record is an internal application log or represents
            an ERROR or CRITICAL state; False if it is a low-priority
            third-party log.
        """
        if record.levelno >= logging.ERROR:
            return True

        is_own_package = record.name == "rs_bidsify" or record.name.startswith(f"{self.package_name}.")

        return is_own_package
