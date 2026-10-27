# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Choose a complete local-calendar range from verified meter history."""

from __future__ import annotations

from datetime import timedelta
from zoneinfo import ZoneInfo

from .history import HistoryValidationError, normalize_stream


def complete_history_dates(stream, commodity, time_zone):
    """Return inclusive local dates; never infer missing observations."""
    intervals = normalize_stream(stream, commodity=commodity)
    if not intervals:
        raise HistoryValidationError("No accepted observations available")
    local = ZoneInfo(time_zone)
    first = intervals[0].start_utc.astimezone(local).date()
    last = intervals[-1].start_utc.astimezone(local).date()
    if (last - first) > timedelta(days=440):
        raise HistoryValidationError(
            "History exceeds the 441-day initial-import limit"
        )
    return first, last
