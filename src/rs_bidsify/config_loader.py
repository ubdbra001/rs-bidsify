import yaml
from importlib import resources


def get_default_config():
    with resources.open_text("rs_bidsify", "defaults.yaml") as f:
        return yaml.safe_load(f)


def deep_merge(base: dict, overrides: dict) -> dict:
    """Recursively merges overrides into base."""
    for key, value in overrides.items():
        if isinstance(value, dict) and key in base:
            base[key] = deep_merge(base[key], value)
        else:
            base[key] = value
    return base


DEMOGRAPHIC_MAPPINGS = {
    "sex": {"u": 0, "unknown": 0, "m": 1, "male": 1, "f": 2, "female": 2},
    "hand": {"r": 1, "right": 1, "l": 2, "left": 2, "a": 3, "ambidextrous": 3},
}

PARTICIPANT_INFO = {
    "dataset": {"sheet_name": 6, "index_col": "participant_id"},
    "codebook": {"sheet_name": 7, "index_col": "Variable"},
}

PHENOTYPE_INFO = {
    "dataset": {"sheet_name": 8, "index_col": "participant_id"},
    "codebook": {"sheet_name": 9, "index_col": "Variable"},
}
