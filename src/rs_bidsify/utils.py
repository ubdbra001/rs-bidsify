from datetime import datetime, timezone

def get_utc_today() -> datetime:
    return datetime.now(timezone.utc)