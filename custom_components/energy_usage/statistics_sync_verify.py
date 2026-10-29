# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Strict read-back verification for an Energy Usage synchronization plan.

Do not treat an accepted Recorder queue operation as persisted data. Call
this after Recorder has committed the import; never assume a delay suffices.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import isclose, isfinite
from typing import Mapping, Sequence

from .statistics_sync_plan import StatisticsSyncError


@dataclass(frozen=True)
class SyncVerification:
    """Evidence that a full Recorder read-back matches the planned series."""

    statistic_id: str
    observations: int
    earliest: datetime
    latest: datetime


def _normal(rows: Sequence[Mapping]) -> dict[datetime, tuple[float, float]]:
    result = {}
    previous = None
    for row in rows:
        stamp = row.get("start")
        if isinstance(stamp, (int, float)) and not isinstance(stamp, bool):
            if not isfinite(stamp):
                raise StatisticsSyncError("Invalid Recorder timestamp")
            stamp = datetime.fromtimestamp(stamp, timezone.utc)
        if (not isinstance(stamp, datetime) or stamp.tzinfo is None
                or stamp.utcoffset() != timedelta(0)):
            raise StatisticsSyncError("Invalid Recorder timestamp")
        stamp = stamp.astimezone(timezone.utc)
        state, total = row.get("state"), row.get("sum")
        if any(not isinstance(v, (int, float)) or isinstance(v, bool)
               or not isfinite(v) or v < 0 for v in (state, total)):
            raise StatisticsSyncError("Invalid Recorder statistic value")
        if previous is not None and stamp <= previous:
            raise StatisticsSyncError("Unordered Recorder statistics")
        result[stamp] = (float(state), float(total))
        previous = stamp
    return result


def verify_sync_persistence(
    statistic_id: str,
    expected: Sequence[Mapping],
    stored: Sequence[Mapping],
    *,
    complete_readback: bool,
    tolerance: float = 1e-6,
) -> SyncVerification:
    """Fail closed on any missing, extra, duplicated or different statistic.

    The caller must obtain a complete read-back from Home Assistant Recorder
    after import completion. This function does not write or wait for Recorder.
    """
    if not statistic_id.startswith("energy_usage:"):
        raise StatisticsSyncError("Foreign statistic identifier")
    if not complete_readback:
        raise StatisticsSyncError("Complete Recorder read-back required")
    if not isfinite(tolerance) or tolerance < 0:
        raise StatisticsSyncError("Invalid verification tolerance")
    planned = _normal(expected)
    actual = _normal(stored)
    if not planned:
        raise StatisticsSyncError("No expected canonical statistics")
    if planned.keys() != actual.keys():
        raise StatisticsSyncError("Recorder dates differ from canonical history")
    for stamp, pair in planned.items():
        found = actual[stamp]
        if any(not isclose(a, b, rel_tol=0, abs_tol=tolerance)
               for a, b in zip(pair, found)):
            raise StatisticsSyncError(
                "Recorder values differ from canonical history"
            )
    stamps = tuple(planned)
    return SyncVerification(statistic_id, len(stamps), stamps[0], stamps[-1])
