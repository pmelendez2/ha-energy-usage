# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Validate complete meter history before guarded Recorder reconciliation.

Manual and scheduled callers must explicitly authorize reconciliation.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from .history import normalize_stream
from .statistics_import import build_statistics
from .statistics_sync_recorder import sync_owned_statistics
from .statistics_sync_plan import StatisticsSyncError
from .statistics_sync_completion import wait_for_persisted_statistics


@dataclass(frozen=True)
class SyncResult:
    """A reconciliation result, including verified persistence status."""

    meter_id: int
    statistic_id: str
    added: int
    corrected: int
    unchanged: int
    queued: bool
    persisted: bool = False
    observations: int = 0


class MeterSyncRuntime:
    """Serialize work on each physical meter, including concurrent requests."""

    def __init__(self):
        self._locks: dict[int, asyncio.Lock] = {}
        self._active: set[asyncio.Task] = set()
        self._closing = False

    def begin_close(self):
        """Reject new meter operations before platform teardown."""
        self._closing = True

    def reopen(self):
        """Allow new work if unloading was unsuccessful."""
        self._closing = False

    async def drain(self):
        """Reject new work and await all admitted operations."""
        self._closing = True
        while self._active:
            await asyncio.gather(
                *tuple(self._active), return_exceptions=True
            )


    async def sync_meter(
        self, hass, api, meter, *, confirmed=False
    ) -> SyncResult:
        """Fetch canonical data; abort before writes on any invalid input."""
        if not confirmed:
            raise StatisticsSyncError("Synchronization requires approval")
        if not isinstance(meter, dict):
            raise StatisticsSyncError("Invalid physical meter")
        try:
            meter_id = int(meter["id"])
            commodity = int(meter["commodity"])
            name = str(meter["display_name"])
        except (KeyError, ValueError, TypeError) as exc:
            raise StatisticsSyncError("Invalid physical meter") from exc
        if meter_id <= 0 or commodity not in (1, 7):
            raise StatisticsSyncError("Unsupported physical meter")
        if self._closing:
            raise StatisticsSyncError("Synchronization runtime is closing")
        task = asyncio.current_task()
        self._active.add(task)
        try:
            return await self._sync_locked(
                hass, api, meter_id, commodity, name
            )
        finally:
            self._active.discard(task)

    async def _sync_locked(self, hass, api, meter_id, commodity, name):
        """Hold the meter lock until persistence verification completes."""
        lock = self._locks.setdefault(meter_id, asyncio.Lock())
        async with lock:
            stream = await api.stream(meter_id)
            if stream.get("physical_meter_id") != meter_id:
                raise StatisticsSyncError("Meter history identity mismatch")
            intervals = normalize_stream(stream, commodity=commodity)
            batch = build_statistics(
                meter_id,
                commodity,
                name,
                intervals,
                time_zone=hass.config.time_zone,
            )
            plan = await sync_owned_statistics(
                hass, batch, confirmed=True
            )
            verified = await wait_for_persisted_statistics(
                hass, batch.statistic_id, plan.rows,
            )
            return SyncResult(
                meter_id=meter_id,
                statistic_id=batch.statistic_id,
                added=plan.added,
                corrected=plan.corrected,
                unchanged=plan.unchanged,
                queued=bool(plan.added or plan.corrected),
                persisted=True,
                observations=verified.observations,
            )
