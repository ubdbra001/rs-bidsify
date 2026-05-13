from datetime import datetime, timezone
from typing import Any


def get_utc_today() -> datetime:
    return datetime.now(timezone.utc)


def locate_dynamic_fields(
    input_obj: dict, target: str = "VARIES", current_path: list | None = None
):
    """Recursively searches through dictionaries to find 'path' to instances of the target"""

    if current_path is None:
        current_path = []

    paths = []

    if isinstance(input_obj, dict):
        for key, val in input_obj.items():
            new_path = current_path + [key]

            if val == target:
                paths.append(new_path)
            elif isinstance(val, dict):
                paths.extend(locate_dynamic_fields(val, target, new_path))

    return paths


def apply_dynamic_value(data: dict[str, Any], path: list[str], new_value: Any):
    """Insert a new value in the nested dictionary by following the 'path'"""
    try:
        current = data
        for key in path[:-1]:
            current = current[key]
        current[path[-1]] = new_value
    except KeyError, TypeError:
        print(f"Error: Path {path} could not be followed.")
