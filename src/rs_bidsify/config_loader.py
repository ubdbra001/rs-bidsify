import yaml
from importlib import resources


def get_default_config():
    with resources.open_text("rs_bidsify", "defaults.yaml") as f:
        return yaml.safe_load(f)


def deep_merge(base: dict, overrides: dict) -> dict:
    """Recursively merges overrides into base."""
    for key, value in overrides.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            base[key] = deep_merge(base[key], value)
        else:
            base[key] = value
    return base
