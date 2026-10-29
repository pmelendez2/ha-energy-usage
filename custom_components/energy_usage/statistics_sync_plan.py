# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Read-only reconciliation plan for empty or populated HA statistics.

No Recorder write is performed. Callers must read back the complete owned
statistic series and prove its baseline before executing any future writes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import isfinite
from typing import Mapping, Sequence


class StatisticsSyncError(ValueError):
    """Recorded or canonical statistic data is unsafe to reconcile."""


@dataclass(frozen=True)
class StatisticsSyncPlan:
    """A complete target series and its changes, never a write instruction."""

    mode: str
    added: int
    corrected: int
    unchanged: int
    rows: tuple[dict, ...]
    first_changed: datetime | None


def _rows(source: Sequence[Mapping], *, canonical: bool) -> list[dict]:
    result = []
    previous = None
    for item in source:
        stamp = item.get("start")
        state = item.get("state")
        total = item.get("sum")
        if (not isinstance(stamp, datetime) or stamp.tzinfo is None
                or stamp.utcoffset() != timedelta(0)
                or not isinstance(state, (int, float))
                or isinstance(state, bool) or not isfinite(state)
                or state < 0 or not isinstance(total, (int, float))
                or isinstance(total, bool) or not isfinite(total)
                or total < 0):
            raise StatisticsSyncError("Invalid statistic timestamp/value")
        stamp = stamp.astimezone(timezone.utc)
        if previous is not None and stamp <= previous:
            raise StatisticsSyncError("Unordered or duplicate statistic")
        result.append({"start": stamp, "state": float(state),
                       "sum": float(total)})
        previous = stamp
    if canonical and not result:
        raise StatisticsSyncError("Canonical history is empty")
    return result


def plan_statistics_sync(
    existing: Sequence[Mapping],
    canonical: Sequence[Mapping],
    *,
    tolerance: float = 1e-7,
) -> StatisticsSyncPlan:
    """Plan a complete replacement without losing any historic observations.

    The canonical input is a verified full-history StatisticsBatch, not a
    bounded API window. Only exact timestamp matches count as the same
    observation. Missing canonical points retain their existing state; this
    deliberately blocks deletion but does not infer any missing values.

    The first existing cumulative sum may include earlier history not present
    in the canonical input. Therefore do not execute this plan until full
    provenance and Recorder read-back are established.
    """
    old = _rows(existing, canonical=False)
    new = _rows(canonical, canonical=True)
    old_by_time = {r["start"]: r for r in old}
    new_by_time = {r["start"]: r for r in new}
    if old and set(old_by_time) - set(new_by_time):
        raise StatisticsSyncError(
            "Canonical history omits existing observations; review required"
        )
    if old:
        common = set(old_by_time) & set(new_by_time)
        if not common:
            raise StatisticsSyncError(
                "Existing statistics do not match canonical history"
            )
    added = corrected = unchanged = 0
    first_changed = None
    for row in new:
        old_row = old_by_time.get(row["start"])
        if old_row is None:
            added += 1
        elif abs(row["state"] - old_row["state"]) > tolerance:
            corrected += 1
        else:
            unchanged += 1
        if (old_row is None or
                abs(row["state"] - old_row["state"]) > tolerance):
            if first_changed is None:
                first_changed = row["start"]
    # The sum must be reconstructed from every canonical observation, not
    # spliced from old cumulative sums after a correction.
    running = 0.0
    target = []
    for row in new:
        running += row["state"]
        target.append({"start": row["start"], "state": row["state"],
                       "sum": running})
    mode = "initial" if not old else "reconcile"
    return StatisticsSyncPlan(
        mode, added, corrected, unchanged, tuple(target), first_changed
    )
