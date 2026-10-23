# SPDX-License-Identifier: MIT
"""Prepare graph-ready long-term statistics from actual utility readings.

No missing data is synthesized; no data is written by this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from decimal import Decimal
from typing import Sequence

from .history import UsageInterval


class StatisticsImportError(ValueError):
    """Reject observations unsuitable for Home Assistant statistics."""


@dataclass(frozen=True)
class StatisticsBatch:
    """Verified readings for one physical meter, ready for Recorder."""

    statistic_id: str
    name: str
    unit: str
    rows: tuple[dict, ...]
    missing_intervals: int


def build_statistics(
    meter_id: int,
    commodity: int,
    meter_name: str,
    intervals: Sequence[UsageInterval],
    *,
    time_zone: str = "UTC",
) -> StatisticsBatch:
    """Prepare ordered statistics; preserve every missing interval as absent.

    Electricity is hourly. Daily gas readings are assigned to their
    local reporting date for display, without changing source times.
    Missing intervals are never synthesized.
    """
    if type(meter_id) is not int or meter_id <= 0:
        raise StatisticsImportError("Invalid meter identity")
    if commodity not in (1, 7):
        raise StatisticsImportError("Unsupported utility type")
    if not meter_name or not meter_name.strip():
        raise StatisticsImportError("Missing meter name")
    unit = "kWh" if commodity == 1 else "therm"
    step = timedelta(hours=1) if commodity == 1 else timedelta(days=1)
    prefix = "electricity" if commodity == 1 else "gas"
    statistic_id = f"energy_usage:{prefix}_meter_{meter_id}"
    total = Decimal(0)
    previous_end: datetime | None = None
    previous_gas_date = None
    try:
        local_tz = ZoneInfo(time_zone)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise StatisticsImportError("Invalid time zone") from exc
    missing = 0
    rows: list[dict] = []
    for reading in sorted(intervals, key=lambda r: r.start_utc):
        start, end = reading.start_utc, reading.end_utc
        if (start.tzinfo is None or start.utcoffset() != timedelta(0)
                or end - start != step or reading.unit != unit
                or not reading.value.is_finite() or reading.value < 0
                or type(reading.revision_id) is not int
                or reading.revision_id <= 0):
            raise StatisticsImportError("Incompatible utility reading")
        if commodity == 1 and (start.minute or start.second
                               or start.microsecond):
            raise StatisticsImportError("Hourly electricity not aligned")
        if commodity == 7:
            local = start.astimezone(local_tz)
            # SDG&E labels daily gas readings at 23:59 local time.
            # This mapping affects display only, never source readings.
            if (local.hour, local.minute, local.second) != (23, 59, 0):
                raise StatisticsImportError(
                    "Unexpected daily gas reporting boundary"
                )
            gas_date = local.date()
            display_start = datetime.combine(
                gas_date, time.min, local_tz
            ).astimezone(timezone.utc)
            if previous_gas_date is not None:
                elapsed_days = (gas_date - previous_gas_date).days
                if elapsed_days <= 0:
                    raise StatisticsImportError(
                        "Duplicate or out-of-order gas reporting date"
                    )
                missing += elapsed_days - 1
            previous_gas_date = gas_date
        else:
            display_start = start
        if previous_end is not None and commodity == 1:
            if start < previous_end:
                raise StatisticsImportError("Overlapping utility readings")
            if start > previous_end:
                missing += int((start - previous_end) / step)
        total += reading.value
        rows.append({
            "start": display_start,
            "state": float(reading.value),
            "sum": float(total),
        })
        previous_end = end
    if not rows:
        raise StatisticsImportError("No validated usage readings")
    return StatisticsBatch(
        statistic_id, meter_name, unit, tuple(rows), missing
    )
