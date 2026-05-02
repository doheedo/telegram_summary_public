from datetime import timezone, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def load_runtime_timezone(timezone_name: str, fallback_for_missing: bool = False):
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        if fallback_for_missing and timezone_name == "Asia/Seoul":
            return timezone(timedelta(hours=9), name="Asia/Seoul")
        raise
