# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Project Contributors
"""Plan usage-history changes without mutating Recorder statistics.

The caller supplies normalized intervals for the same physical meter.
Missing intervals in a bounded response do not imply deletion: a
partial import, a data gap, and an intentionally omitted window may
all produce the same absence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol, Sequence


class IntervalLike(Protocol):
    """Fields provided by a normalized usage interval."""

    start_utc: datetime
    end_utc: datetime
    value: Decimal
    unit: str
    revision_id: int


@dataclass(frozen=True)
class ChangePlan:
    """Validated additions, accepted corrections, and unchanged rows."""

    added: tuple[IntervalLike, ...]
    corrected: tuple[IntervalLike, ...]
    unchanged: tuple[IntervalLike, ...]


def _index(
    intervals: Sequence[IntervalLike],
) -> dict[tuple[datetime, datetime], IntervalLike]:
    """Reject ambiguous or overlapping intervals before planning."""
    result: dict[tuple[datetime, datetime], IntervalLike] = {}
    ordered = sorted(intervals, key=lambda item: item.start_utc)
    prior_end: datetime | None = None
    for row in ordered:
        if row.start_utc.tzinfo is None or row.end_utc.tzinfo is None:
            raise ValueError("Usage timestamps must be timezone-aware")
        if row.end_utc <= row.start_utc:
            raise ValueError("Usage interval duration must be positive")
        if prior_end is not None and row.start_utc < prior_end:
            raise ValueError("Usage intervals overlap")
        if not isinstance(row.value, Decimal) or not row.value.is_finite():
            raise ValueError("Usage value must be a finite Decimal")
        if row.value < 0:
            raise ValueError("Negative consumption requires explicit policy")
        if row.unit not in ("kWh", "therm"):
            raise ValueError("Unsupported usage unit")
        if type(row.revision_id) is not int or row.revision_id <= 0:
            raise ValueError("Invalid accepted revision")
        key = (row.start_utc, row.end_utc)
        if key in result:
            raise ValueError("Duplicate usage interval")
        result[key] = row
        prior_end = row.end_utc
    return result


def plan_usage_changes(
    stored: Sequence[IntervalLike],
    incoming: Sequence[IntervalLike],
) -> ChangePlan:
    """Identify additions and corrections for a physical meter.

    A newer revision with the same consumption is unchanged.
    A different consumption value is a correction.
    A changed duration requires further validation before updating history.
    Missing incoming readings never delete stored readings.

    This function reports differences only: it does not update Home
    Assistant statistics, remove readings, or calculate billing amounts.
    """
    old = _index(stored)
    new = _index(incoming)
    units = {row.unit for row in (*stored, *incoming)}
    if len(units) > 1:
        raise ValueError("Cannot reconcile different consumption units")

    old_by_start = {row.start_utc: row for row in stored}
    added: list[IntervalLike] = []
    corrected: list[IntervalLike] = []
    unchanged: list[IntervalLike] = []
    for key, row in sorted(new.items()):
        previous = old.get(key)
        if previous is None:
            if row.start_utc in old_by_start:
                raise ValueError("Changed interval duration needs review")
            added.append(row)
        elif row.value != previous.value:
            corrected.append(row)
        else:
            unchanged.append(row)

    return ChangePlan(tuple(added), tuple(corrected), tuple(unchanged))
