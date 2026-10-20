# SPDX-License-Identifier: MIT
"""Prepare a read-only Recorder statistics preview under ADR-0001.

This module does not call Recorder, persist progress, clear statistics,
write SQL, or claim that external statistics have been imported.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .statistics_plan import StatisticsPlan


@dataclass(frozen=True)
class StatisticsPreview:
    """Meter-specific preview suitable for dry-run review."""

    statistic_id: str
    metadata: dict
    statistics: tuple[dict, ...]
    incomplete_hours: tuple[str, ...]


def electricity_statistic_id(meter_id: int) -> str:
    """Return a meter-ID-based external identifier, never a display name."""
    if type(meter_id) is not int or meter_id <= 0:
        raise ValueError("Invalid physical meter ID")
    return f"energy_usage:electricity_meter_{meter_id}"


def preview_electricity(meter_id: int, plan: StatisticsPlan) -> StatisticsPreview:
    """Build finite, validated Recorder-shaped metadata and points.

    Producing a preview does not imply a safe synchronization checkpoint.
    Callers must establish meter ownership and completeness separately.
    """
    statistic_id = electricity_statistic_id(meter_id)
    stats: list[dict] = []
    previous = None
    for point in plan.points:
        if previous is not None and point.start <= previous:
            raise ValueError("Statistics must have increasing timestamps")
        if not isinstance(point.sum, Decimal) or not point.sum.is_finite():
            raise ValueError("Statistics must contain finite sums")
        if point.sum < 0:
            raise ValueError("Negative cumulative consumption")
        stats.append({"start": point.start, "sum": float(point.sum)})
        previous = point.start
    metadata = {
        "statistic_id": statistic_id,
        "source": "energy_usage",
        "name": f"Electricity meter {meter_id}",
        "unit_of_measurement": "kWh",
        "unit_class": "energy",
        "has_sum": True,
        "mean_type": 0,
    }
    return StatisticsPreview(
        statistic_id,
        metadata,
        tuple(stats),
        tuple(hour.isoformat() for hour in plan.incomplete_hours),
    )
