# SPDX-License-Identifier: MIT
"""Guarded Home Assistant Recorder adapter for ADR-0001.

Only an explicitly approved initial import into an empty owned series is
supported. Corrections and rebuilds require a separate transactional protocol.
No writing occurs during normal config-entry setup or polling.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import isclose, isfinite
from typing import Callable, Mapping, Sequence

from .statistics_preview import StatisticsPreview


class RecorderSafetyError(ValueError):
    """A Recorder modification cannot be proven safe."""


@dataclass(frozen=True)
class RecorderImportBatch:
    """Validated initial import, not a confirmation of Recorder persistence."""

    statistic_id: str
    metadata: dict
    rows: tuple[dict, ...]


def prepare_initial_import(
    preview: StatisticsPreview,
    existing: Sequence[Mapping],
    *,
    confirmed: bool = False,
) -> RecorderImportBatch:
    """Allow only a confirmed, complete, empty-series initial import.

    `existing` must come from an authoritative read of the entire series.
    Callers must not pass a time-window subset and assume it is empty.
    """
    if not confirmed:
        raise RecorderSafetyError("Explicit initial-import approval required")
    if existing:
        raise RecorderSafetyError("Series exists; repair protocol required")
    meta = dict(preview.metadata)
    stat_id = preview.statistic_id
    if (not stat_id.startswith("energy_usage:electricity_meter_")
            or meta.get("statistic_id") != stat_id
            or meta.get("source") != "energy_usage"
            or meta.get("unit_of_measurement") != "kWh"
            or meta.get("unit_class") != "energy"
            or meta.get("has_sum") is not True
            or meta.get("mean_type") != 0):
        raise RecorderSafetyError("Invalid or unowned statistic metadata")
    if preview.incomplete_hours:
        # A complete history must be requested before import; gaps are
        # allowed, but callers must explicitly review their existence.
        raise RecorderSafetyError("Incomplete hours need separate review")
    rows = []
    previous: datetime | None = None
    previous_sum = 0.0
    for row in preview.statistics:
        stamp, total = row.get("start"), row.get("sum")
        if (not isinstance(stamp, datetime) or stamp.tzinfo is None
                or stamp.utcoffset() != timedelta(0)
                or stamp.minute or stamp.second or stamp.microsecond
                or not isinstance(total, (int, float))
                or isinstance(total, bool) or not isfinite(total)
                or total < previous_sum or total < 0):
            raise RecorderSafetyError("Unsafe Recorder statistic row")
        if previous is not None and stamp <= previous:
            raise RecorderSafetyError("Unordered Recorder statistic rows")
        rows.append({"start": stamp.astimezone(timezone.utc), "sum": total})
        previous, previous_sum = stamp, float(total)
    if not rows:
        raise RecorderSafetyError("No complete intervals to import")
    return RecorderImportBatch(stat_id, meta, tuple(rows))


def queue_initial_import(hass, batch: RecorderImportBatch) -> None:
    """Queue HA's supported external-statistics import API.

    This function is opt-in; it does not confirm persistence. The caller
    must read back results before reporting completion.
    """
    from homeassistant.components.recorder.statistics import (
        async_add_external_statistics,
    )

    async_add_external_statistics(
        hass, batch.metadata, list(batch.rows)
    )


def verify_import(
    batch: RecorderImportBatch,
    stored: Sequence[Mapping],
    *,
    tolerance: float = 1e-8,
) -> None:
    """Compare read-back values, rejecting omitted or unexpected rows."""
    if len(batch.rows) != len(stored):
        raise RecorderSafetyError("Recorder row count mismatch")
    for expected, actual in zip(batch.rows, stored):
        when = actual.get("start")
        if isinstance(when, (float, int)) and not isinstance(when, bool):
            when = datetime.fromtimestamp(when, timezone.utc)
        if when != expected["start"]:
            raise RecorderSafetyError("Recorder timestamp mismatch")
        number = actual.get("sum")
        if (not isinstance(number, (float, int))
                or isinstance(number, bool) or not isfinite(number)
                or not isclose(number, expected["sum"],
                               rel_tol=0, abs_tol=tolerance)):
            raise RecorderSafetyError("Recorder cumulative sum mismatch")
