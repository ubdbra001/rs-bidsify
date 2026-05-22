from datetime import UTC, datetime
from typing import Any


def get_utc_today() -> datetime:
    """
    Get the current date and time in UTC.

    Returns
    -------
    datetime
        The current UTC timestamp with timezone awareness.
    """
    return datetime.now(UTC)


def locate_dynamic_fields(input_obj: dict, target: str = "VARIES", current_path: list | None = None) -> list:
    """
    Recursively search a dictionary for paths to a specific target value.

    Parameters
    ----------
    input_obj : dict
        The dictionary or nested structure to search through.
    target : str, optional
        The sentinel value indicating a field needs to be dynamically updated.
        Defaults to "VARIES".
    current_path : list of str, optional
        The breadcrumb trail of keys used during recursion. Internal use only.

    Returns
    -------
    list of list of str
        A list of paths, where each path is represented as a list of keys
        leading to an instance of the target.
    """
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
    """
    Insert a new value into a nested dictionary by following a specified path.

    Parameters
    ----------
    data : dict
        The dictionary to be modified in-place.
    path : list of str
        The sequence of keys representing the path to the target field.
    new_value : Any
        The value to be assigned to the field at the end of the path.

    Raises
    ------
    KeyError, TypeError
        If the path does not exist or an intermediate value is not a dictionary.
    """
    try:
        current = data
        for key in path[:-1]:
            current = current[key]
        current[path[-1]] = new_value
    except (KeyError, TypeError):
        print(f"Error: Path {path} could not be followed.")
