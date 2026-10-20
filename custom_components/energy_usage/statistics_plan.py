# SPDX-License-Identifier: MIT
"""Deterministic hourly electricity statistics from accepted observations.

ADR-0001: incomplete hours remain absent; source intervals are unchanged.
No Home Assistant imports or writes occur in this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Protocol, Sequence


class IntervalLike(Protocol):
    """A previously normalized, accepted interval."""

    start_utc: datetime
    end_utc: datetime
    value: Decimal
    unit: str
    revision_id: int


@dataclass(frozen=True)
class StatisticPoint:
    """An observed complete UTC hour and its cumulative consumption."""

    start: datetime
    state: Decimal
    sum: Decimal


@dataclass(frozen=True)
class StatisticsPlan:
    """Read-only plan with explicitly incomplete UTC hours."""

    points: tuple[StatisticPoint, ...]
    incomplete_hours: tuple[datetime, ...]


class StatisticsPlanError(ValueError):
    """The accepted stream is not safe to aggregate."""


def _validate(row: IntervalLike) -> None:
    """Reject invalid or ambiguous source intervals without coercion."""
    start, end = row.start_utc, row.end_utc
    if (not isinstance(start, datetime) or
            not isinstance(end, datetime) or
            start.tzinfo is None or end.tzinfo is None or
            start.utcoffset() != timedelta(0) or
            end.utcoffset() != timedelta(0) or
            start.microsecond or end.microsecond or
            start.second or end.second or start >= end):
        raise StatisticsPlanError("Invalid UTC source interval")
    if row.unit != "kWh":
        raise StatisticsPlanError("Expected normalized electricity kWh")
    if (not isinstance(row.value, Decimal) or
            not row.value.is_finite() or row.value < 0):
        raise StatisticsPlanError("Invalid consumption value")
    if type(row.revision_id) is not int or row.revision_id <= 0:
        raise StatisticsPlanError("Invalid accepted revision")
    # Intervals spanning an hourly boundary require a separate, verified
    # distribution policy. Splitting their consumption would infer data.
    hour_start = start.replace(minute=0, second=0, microsecond=0)
    if end > hour_start + timedelta(hours=1):
        raise StatisticsPlanError("Observation crosses an hourly boundary")


def plan_electricity_hours(
    intervals: Sequence[IntervalLike],
) -> StatisticsPlan:
    """Aggregate fully covered UTC hours, recording partial hours as gaps.

    Supported source cadences are inferred from actual timestamp coverage,
    not from a provider assumption. Adjacent variable-length intervals are
    valid if they cover one hour exactly, without overlap. No partial sum
    is presented as a complete-hour statistic.
    """
    ordered = sorted(intervals, key=lambda row: row.start_utc)
    by_hour: dict[datetime, list[IntervalLike]] = {}
    previous_end: datetime | None = None
    for row in ordered:
        _validate(row)
        if previous_end is not None and row.start_utc < previous_end:
            raise StatisticsPlanError("Overlapping or duplicate observations")
        hour = row.start_utc.replace(minute=0, second=0, microsecond=0)
        by_hour.setdefault(hour, []).append(row)
        previous_end = row.end_utc

    cumulative = Decimal(0)
    points: list[StatisticPoint] = []
    incomplete: list[datetime] = []
    for hour, rows in sorted(by_hour.items()):
        cursor = hour
        total = Decimal(0)
        for row in rows:
            if row.start_utc != cursor:
                incomplete.append(hour)
                break
            cursor = row.end_utc
            total += row.value
        else:
            if cursor != hour + timedelta(hours=1):
                incomplete.append(hour)
                continue
            cumulative += total
            points.append(StatisticPoint(hour, cumulative, cumulative))
    return StatisticsPlan(tuple(points), tuple(incomplete))


def plan_hourly_electricity(
    intervals: Sequence[IntervalLike],
) -> tuple[StatisticPoint, ...]:
    """Backward-compatible hourly result for completed observations."""
    return plan_electricity_hours(intervals).points
