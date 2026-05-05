import logging
import colorlog
from pathlib import Path

def setup_file_handler(root_path: Path, logger: logging.Logger, level: str | int = "INFO"):
    """_summary_

    Parameters
    ----------
    root_path : Path
        _description_
    logger : logging.Logger
        _description_
    level : str | int, optional
        _description_, by default "INFO"
    """

    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | [%(filename)s:%(lineno)d] | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler = logging.FileHandler(root_path / "log.log")
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)

    logger.addHandler(file_handler)

def setup_stream_handler(logger: logging.Logger,level: str | int = logging.INFO):

    stream_formatter = colorlog.ColoredFormatter(
        '%(asctime)s | %(log_color)s%(levelname)-8s%(reset)s | [%(filename)s:%(lineno)d] | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    stream_handler = colorlog.StreamHandler()
    stream_handler.setFormatter(stream_formatter)
    stream_handler.setLevel(level)
    logger.addHandler(stream_handler)

def adjust_mne_logger(level):
    mne_logger = logging.getLogger('mne')
    mne_logger.handlers = []
    mne_logger.propagate = True
    mne_logger.setLevel(level)

def setup_logging(root_path: Path, level: str | int = logging.INFO):

    adjust_mne_logger(level)

    logger = logging.getLogger()
    logger.setLevel(level)
    
    logging.captureWarnings(True)
    
    setup_file_handler(root_path, logger, level)
    setup_stream_handler(logger, level)
