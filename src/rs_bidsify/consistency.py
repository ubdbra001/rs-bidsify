import logging
from typing import Any, Iterable

logger = logging.getLogger(__name__)


def loc_in_participant_data(locations: dict[str, str], part_data_cols: list[str]):
    """Check to ensure that any locations mentioned in the variable fields map are present in the participant data"""

    expected_cols = set(locations.values())
    missing_cols = expected_cols.difference(part_data_cols)

    if missing_cols:
        raise ValueError(
            f"The following columns are listed in the variable fields section of the metadata, "
            f"but not present in the participant data: {','.join(missing_cols)}"
        )


def check_mapping_alignment(
    actual: Iterable[str],
    expected: dict[str, Any],
    context: str,
    strict_symmetry: bool = False,
) -> dict[str, Any]:
    """
    Validate alignment between metadata specifications and actual data content.

    Compares expected keys from metadata against labels physically present in the 
    recording to identify overlaps, missing entries, and unexpected extras.

    Parameters
    ----------
    actual : Iterable[str]
        The labels physically present in the raw data (e.g., channel names).
    expected : dict[str, Any]
        The desired mappings defined in the metadata.
    context : str
        Label used for logging (e.g., "Channels", "Events").
    strict_symmetry : bool, default False
        If False, only warns about metadata keys missing from the data. 
        If True, also warns about data labels missing from the metadata.

    Returns
    -------
    dict[str, Any]
        A subset of the `expected` dictionary containing only the keys 
        found in the `actual` data.
    """
    actual_set = set(actual)
    expected_set = set(expected.keys())

    present = expected_set.intersection(actual_set)
    missing = expected_set.difference(actual_set)
    extra = actual_set.difference(expected_set)

    if present:
        logger.info(f"Specified {context} found in recording: {', '.join(present)}")

    if missing:
        logger.warning(f"{context} in Metadata missing from data: {', '.join(missing)}")

    if strict_symmetry and extra:
        logger.warning(f"{context} in Data not defined in metadata: {', '.join(extra)}")

    return {k: v for k, v in expected.items() if k in present}
