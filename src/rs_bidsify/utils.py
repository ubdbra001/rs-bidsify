from datetime import datetime, timezone
from pathlib import Path

def get_utc_today() -> datetime:
    return datetime.now(timezone.utc)


def find_file(path: Path, ext: str):
    found_path = list(path.glob(f"*.{ext}"))

    if len(found_path) != 1:
        raise ValueError(
            f"Expected single {ext} file in {path}, instead found {len(found_path)}"
        )

    return found_path[0]


