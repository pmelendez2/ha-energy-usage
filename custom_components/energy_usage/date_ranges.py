# SPDX-License-Identifier: MIT
"""Convert customer calendar dates into local-day UTC boundaries."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def selected_calendar_dates_utc(
    start_day: date, end_day: date, time_zone: str
) -> tuple[datetime, datetime]:
    """Return [start, end) in UTC for inclusive local calendar dates.

    End is the following local midnight, not start + N * 24h;
    this preserves daylight-saving days of 23 or 25 hours.
    """
    if end_day < start_day:
        raise ValueError("End date must not precede start date")
    if not isinstance(time_zone, str) or not time_zone:
        raise ValueError("Home Assistant time zone must be configured")
    try:
        local_zone = ZoneInfo(time_zone)
    except (ZoneInfoNotFoundError, ValueError, TypeError) as exc:
        raise ValueError("Invalid Home Assistant time zone") from exc
    begin = datetime.combine(start_day, time.min, local_zone)
    stop = datetime.combine(
        end_day + timedelta(days=1), time.min, local_zone
    )
    return begin.astimezone(timezone.utc), stop.astimezone(timezone.utc)
