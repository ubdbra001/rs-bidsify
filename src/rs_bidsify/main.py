import logging
from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.console import Console
from rich.table import Table
from rich.text import Text

from rs_bidsify import __version__
from rs_bidsify.app_logging import setup_logging
from rs_bidsify.processing import process_dataset

logger = logging.getLogger(__name__)

console = Console()

app = typer.Typer(help="RS-BIDSify: Standardizing resting-state EEG data into BIDS format.", no_args_is_help=True)


def version_callback(value: bool):
    """
    Handle the eager evaluation of the application version flag.

    Prints the application's current semantic version string and cleanly
    terminates execution if the flag is provided.

    Parameters
    ----------
    value : bool
        The boolean flag evaluated by Typer determining if the version
        was requested.

    Raises
    ------
    typer.Exit
        Cleanly exits the application context after displaying the version.
    """
    if value:
        typer.echo(f"RS-BIDSify verson: {__version__}")
        raise typer.Exit()


@app.command(no_args_is_help=True)
def convert(
    raw_data_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the input directory containing raw source data",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
        ),
    ],
    bids_data_path: Annotated[
        Path,
        typer.Argument(
            help="Output directory where the BIDS-formatted data will be saved",
            writable=True,
        ),
    ],
    config_file: Annotated[
        typer.FileText | None,
        typer.Option("--config", help="User YAML configuration file"),
    ] = None,
    log_path: Annotated[
        Path | None,
        typer.Option(
            "--logs",
            help="Location for logs (defaults to '../logs' relative to raw_data_path)",
            exists=True,
            dir_okay=True,
            file_okay=False,
            writable=True,
        ),
    ] = None,
):
    """
    Execute the full end-to-end raw EEG to BIDS conversion pipeline.

    This command orchestrates the entire structural data transformation. It
    validates input source files, parses demographic indices, maps string
    variables to standardized formats, reads and modifies recording-level MNE
    objects, and writes the standardized BIDS file hierarchy to disk.
    Additionally, it runs post-conversion synchronization routines to prune
    failed subjects from the participant index and phenotype data files.

    Parameters
    ----------
    raw_data_path : Path
        The source directory containing raw data to be converted. Checked for
        readability and structural validity.
    bids_data_path : Path
        The destination directory for the BIDS dataset. Created automatically
        if it does not yet exist.
    config_file : FileText, optional
        A user-provided text stream pointing to a YAML file containing
        configuration overrides.
    log_path : Path, optional
        The directory where application runtime files will be generated. Defaults
        to a 'logs' folder adjacent to the raw data path if unprovided.

    Returns
    -------
    None
        Orchestrates the conversion pipeline and outputs side-effects directly
        to the terminal and filesystem logs.
    """
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

    results = process_dataset(raw_data_path, bids_data_path, user_overrides)

    logger.info(f"Successfully BIDSified data from {raw_data_path}, written to {bids_data_path}")

    show_results_summary(results)


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show the installed version of RS-BIDSify",
    ),
):
    """Global entry point and configuration callback for RS-BIDSify."""
    pass


def show_results_summary(results: list[dict]):
    table = Table(title="RS-BIDSify results summary")
    table.add_column("Subject")
    table.add_column("Task")
    table.add_column("Status")
    table.add_column("Errors")

    status_fmt = {
        "Success": {"style": "green"},
        "Skipped": {"style": "cyan"},
        "Failed": {"style": "red"},
    }

    for result in results:
        recording, status, error = (result["recording"], result["status"], result["error"])

        style_kwargs = status_fmt.get(status, {})
        formatted_status = Text(status, **style_kwargs)  # pyright: ignore[reportArgumentType]

        table.add_row(recording.subject, recording.task, formatted_status, error)

    console.print(table)


if __name__ == "__main__":
    app()
