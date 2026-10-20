# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Project Contributors
"""Read authenticated usage windows without synthesizing missing data."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .api import EnergyApi, EnergyApiError
from .history import UsageInterval, normalize_stream


async def fetch_usage_history(
    api: EnergyApi,
    meter_id: int,
    commodity: int,
    start: datetime,
    end: datetime,
) -> list[UsageInterval]:
    """Fetch actual observations using contiguous UTC windows.

    The interval start determines its window. No data is interpolated,
    and this function never modifies Home Assistant Recorder.
    """
    if (
        not isinstance(start, datetime)
        or not isinstance(end, datetime)
        or start.tzinfo is None
        or end.tzinfo is None
        or start.utcoffset() != timedelta(0)
        or end.utcoffset() != timedelta(0)
        or start.microsecond
        or end.microsecond
        or start >= end
    ):
        raise ValueError("Expected increasing, whole-second UTC bounds")

    result: list[UsageInterval] = []
    cursor = start.astimezone(timezone.utc)
    stop = end.astimezone(timezone.utc)
    while cursor < stop:
        next_end = min(cursor + timedelta(days=31), stop)
        response = await api.window(meter_id, cursor, next_end)
        normalized = normalize_stream(response, commodity=commodity)
        for item in normalized:
            if not cursor <= item.start_utc < next_end:
                raise EnergyApiError("Observation lies outside its window")
            if result and item.start_utc < result[-1].end_utc:
                raise EnergyApiError("Windows contain overlapping readings")
            result.append(item)
        cursor = next_end
    return result
