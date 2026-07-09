from importlib import resources

import yaml


def load_config(config_override: dict | None = None) -> dict:
    """
    Combine default configuration settings with user-provided overrides.

    This function retrieves the base configuration using `get_default_config`
    and applies a deep merge with any user-supplied overrides. The values
    within the override dictionary take precedence over the defaults, allowing
    granular customization of the BIDS conversion pipeline.

    Parameters
    ----------
    config_override : dict, optional
        A dictionary containing user-defined configuration keys and values.
        Defaults to None, in which case only the base configuration is returned.

    Returns
    -------
    dict
        The fully resolved and merged configuration dictionary.
    """
    config = get_default_config()

    if config_override:
        config = deep_merge(config, config_override)

    return config


def get_default_config() -> dict:
    """
    Load the default configuration settings from the package resources.

    Reads and parses the 'defaults.yaml' file bundled within the
    'rs_bidsify' package.

    Returns
    -------
    dict
        The configuration settings parsed from YAML.
    """
    with resources.open_text("rs_bidsify", "defaults.yaml") as f:
        return yaml.safe_load(f)


def deep_merge(base: dict, overrides: dict) -> dict:
    """
    Recursively merge the contents of the overrides dictionary into the base dictionary.

    For keys that exist in both dictionaries, if both values are dictionaries,
    the function calls itself recursively. Otherwise, the value from the
    overrides dictionary replaces the value in the base dictionary.

    Parameters
    ----------
    base : dict
        The initial dictionary to be updated. This object is modified in-place.
    overrides : dict
        The dictionary containing new values or nested updates to apply.

    Returns
    -------
    dict
        The updated base dictionary after the recursive merge.
    """
    for key, value in overrides.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            base[key] = deep_merge(base[key], value)
        else:
            base[key] = value
    return base
