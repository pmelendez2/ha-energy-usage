# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Guarded Recorder read/plan/write adapter for canonical statistics.

Both scheduled and manual callers must supply verified canonical data and
explicitly authorize the synchronization operation.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import isclose, isfinite

from .statistics_sync_plan import (
    StatisticsSyncError,
    plan_statistics_sync,
)


def normalize_recorder_rows(source):
    """Normalize Recorder rows, including gas DST-shifted UTC starts."""
    result = []
    for row in source:
        start = row.get("start")
        if isinstance(start, (int, float)) and not isinstance(start, bool):
            if not isfinite(start):
                raise StatisticsSyncError("Invalid Recorder timestamp")
            start = datetime.fromtimestamp(start, timezone.utc)
        if (not isinstance(start, datetime) or start.tzinfo is None
                or start.utcoffset() != timedelta(0)):
            raise StatisticsSyncError("Invalid Recorder timestamp")
        if "state" not in row or "sum" not in row:
            raise StatisticsSyncError("Recorder row missing state or sum")
        result.append({
            "start": start,
            "state": row["state"],
            "sum": row["sum"],
        })
    return result


def validate_owned_baseline(existing, canonical, *, tolerance=1e-6):
    """Reject an unrelated or truncated existing Recorder series.

    Corrected *state* values may differ, but the first recorded cumulative
    sum must equal the original canonical sum unless the first observation
    itself was corrected. Such an ambiguous first correction is deferred.
    """
    if not existing:
        return
    if not canonical:
        raise StatisticsSyncError("Canonical history unavailable")
    if existing[0]["start"] != canonical[0]["start"]:
        raise StatisticsSyncError("Recorder baseline differs from source")
    if not isclose(existing[0]["sum"], canonical[0]["sum"],
                   rel_tol=0, abs_tol=tolerance):
        raise StatisticsSyncError(
            "First cumulative observation differs; review required"
        )


async def read_owned_statistics(hass, statistic_id, start, end):
    """Read the full owned series via Home Assistant's Recorder API."""
    if not statistic_id.startswith("energy_usage:"):
        raise StatisticsSyncError("Statistic is not owned by Energy Usage")
    if not start < end:
        raise StatisticsSyncError("Invalid Recorder read range")
    from homeassistant.components.recorder import get_instance
    from homeassistant.components.recorder.statistics import (
        statistics_during_period,
    )

    rows = await get_instance(hass).async_add_executor_job(
        statistics_during_period,
        hass,
        start,
        end,
        {statistic_id},
        "hour",
        None,
        {"state", "sum"},
    )
    result = normalize_recorder_rows(rows.get(statistic_id, []))
    if statistic_id.startswith("energy_usage:electricity_"):
        if any(r["start"].minute or r["start"].second
               or r["start"].microsecond for r in result):
            raise StatisticsSyncError("Electricity hour is not aligned")
    return result


async def sync_owned_statistics(hass, batch, *, confirmed=False):
    """Read, plan and queue a verified canonical full-history series.

    Caller must provide an accepted, complete StatisticsBatch. Recorder
    writes are queued, not immediately committed. No success or persistence
    claim may be made until separate read-back verification finishes.
    """
    if not confirmed:
        raise StatisticsSyncError("Explicit synchronization approval needed")
    if not batch.statistic_id.startswith("energy_usage:"):
        raise StatisticsSyncError("Statistic source is not Energy Usage")
    if not batch.rows:
        raise StatisticsSyncError("No verified canonical observations")
    if batch.unit not in ("kWh", "thm", "therm"):
        raise StatisticsSyncError("Unsupported statistic unit")
    canonical = tuple(batch.rows)
    # Starts at epoch to prove there are no earlier Recorder observations.
    beginning = datetime(1970, 1, 1, tzinfo=timezone.utc)
    ending = max(datetime.now(timezone.utc), canonical[-1]["start"])
    ending += timedelta(days=2)
    existing = await read_owned_statistics(
        hass, batch.statistic_id, beginning, ending
    )
    validate_owned_baseline(existing, canonical)
    plan = plan_statistics_sync(existing, canonical)
    if not plan.added and not plan.corrected:
        return plan
    from homeassistant.components.recorder.models import (
        StatisticData,
        StatisticMeanType,
        StatisticMetaData,
    )
    from homeassistant.components.recorder.statistics import (
        async_add_external_statistics,
    )

    meta = StatisticMetaData(
        has_sum=True,
        mean_type=StatisticMeanType.NONE,
        name=f"{batch.name} usage",
        source="energy_usage",
        statistic_id=batch.statistic_id,
        unit_class="energy",
        unit_of_measurement="kWh" if batch.unit == "kWh" else "thm",
    )
    # HA's external import updates matching timestamps and inserts new ones.
    # Supply the complete cumulative series so corrections propagate forward.
    async_add_external_statistics(
        hass, meta, [StatisticData(**row) for row in plan.rows]
    )
    return plan
