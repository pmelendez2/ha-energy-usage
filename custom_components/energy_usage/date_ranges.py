# SPDX-License-Identifier: MIT
"""Convert customer calendar dates into local-day UTC boundaries."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone, tzinfo


def selected_calendar_dates_utc(
    start_day: date, end_day: date, local_tz: tzinfo
) -> tuple[datetime, datetime]:
    """Return [start, end) in UTC for inclusive local calendar dates.

    End is the following local midnight, not start + N * 24h;
    this preserves daylight-saving days of 23 or 25 hours.
    """
    if end_day < start_day:
        raise ValueError("End date must not precede start date")
    if not isinstance(local_tz, tzinfo):
        raise ValueError("A configured time zone object is required")
    begin = datetime.combine(start_day, time.min, local_tz)
    stop = datetime.combine(
        end_day + timedelta(days=1), time.min, local_tz
    )
    return begin.astimezone(timezone.utc), stop.astimezone(timezone.utc)
