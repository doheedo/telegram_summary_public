from datetime import datetime, timedelta

from app.timezones import load_runtime_timezone


def test_load_runtime_timezone_returns_requested_zone():
    tz = load_runtime_timezone("UTC")

    assert tz.key == "UTC"


def test_load_runtime_timezone_falls_back_for_asia_seoul():
    tz = load_runtime_timezone("Asia/Seoul", fallback_for_missing=True)

    assert datetime(2026, 4, 22, 7, 0, tzinfo=tz).utcoffset() == timedelta(hours=9)
