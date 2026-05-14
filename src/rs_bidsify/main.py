import logging
import typer
import yaml

from pathlib import Path
from typing import Annotated, Optional

from rs_bidsify.app_logging import setup_logging
from rs_bidsify.processing import process_dataset

logger = logging.getLogger(__name__)

app = typer.Typer()

@app.command()
def main(
    raw_data_path: Annotated[Path, typer.Argument(
        help="Path to the input directory containing raw source data",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True)],
    bids_data_path: Annotated[Path, typer.Argument(
        help="Output directory where the BIDS-formatted data will be saved",
        writable=True)],
    config_file: Annotated[Optional[typer.FileText], typer.Option("--config",
        help="User YAML configuration file"
    )] = None, 
    log_path: Annotated[Optional[Path], typer.Option("--logs",
        help="Location for logs (defaults to '../logs' relative to raw_data_path)",
        exists=True,
        dir_okay=True,
        file_okay=False,
        writable=True
    )] = None
):
    if log_path is None:
        log_path = raw_data_path.parent / "logs"

    user_overrides = {}

    if config_file:
        user_overrides = yaml.safe_load(config_file)
    
    setup_logging(log_path)

    logger.info("Starting RS-BIDSify")

    logger.info(f"Logs will be written to {log_path}")
    
    if not bids_data_path.exists():
        logger.warning(f"Creating output directory: {bids_data_path}")
        bids_data_path.mkdir(parents=True)
    
    process_dataset(raw_data_path, bids_data_path, user_overrides)

    logger.info(f"Successfully BIDSified data from {raw_data_path}, written to {bids_data_path}")

if __name__ == "__main__":
    app()