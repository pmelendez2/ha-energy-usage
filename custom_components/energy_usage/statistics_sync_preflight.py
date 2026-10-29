# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Read-only synchronization assessment against actual HA Recorder history.

Never queue writes. This preflight works on empty and populated statistics.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .history import normalize_stream
from .statistics_import import build_statistics
from .statistics_sync_plan import plan_statistics_sync, StatisticsSyncError
from .statistics_sync_recorder import (
    read_owned_statistics,
    validate_owned_baseline,
)


@dataclass(frozen=True)
class SyncPreflight:
    """Read-only comparison; not evidence that any write has committed."""

    statistic_id: str
    meter_id: int
    existing: int
    canonical: int
    added: int
    corrected: int
    unchanged: int
    first_changed: datetime | None


async def assess_meter(hass, api, meter, *, read_statistics=None):
    """Compare full authoritative history with complete Recorder history.

    A mismatched or incomplete historical baseline aborts without writes.
    """
    try:
        meter_id = int(meter["id"])
        commodity = int(meter["commodity"])
        name = str(meter["display_name"])
    except (TypeError, KeyError, ValueError) as exc:
        raise StatisticsSyncError("Invalid meter metadata") from exc
    if meter_id <= 0 or commodity not in (1, 7):
        raise StatisticsSyncError("Unsupported meter")
    stream = await api.stream(meter_id)
    if stream.get("resolved") is not True or stream.get("issues"):
        raise StatisticsSyncError("Canonical meter history is not resolved")
    if stream.get("physical_meter_id") != meter_id:
        raise StatisticsSyncError("Canonical meter identity mismatch")
    intervals = normalize_stream(stream, commodity=commodity)
    batch = build_statistics(
        meter_id, commodity, name, intervals,
        time_zone=hass.config.time_zone,
    )
    earliest = datetime(1970, 1, 1, tzinfo=timezone.utc)
    latest = max(datetime.now(timezone.utc), batch.rows[-1]["start"])
    latest += timedelta(days=2)
    reader = read_statistics or read_owned_statistics
    existing = await reader(hass, batch.statistic_id, earliest, latest)
    validate_owned_baseline(existing, batch.rows)
    plan = plan_statistics_sync(existing, batch.rows)
    return SyncPreflight(
        batch.statistic_id, meter_id, len(existing),
        len(batch.rows), plan.added, plan.corrected, plan.unchanged,
        plan.first_changed,
    )
