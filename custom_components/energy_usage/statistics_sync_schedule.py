# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Automatically reconcile canonical meter usage with HA Recorder.

Failed cycles retry at the next interval; they never alter canonical input.
"""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import callback
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.helpers.event import (
    async_call_later,
    async_track_time_interval,
)

from .const import DOMAIN
from .statistics_sync_service import sync_one
from .statistics_sync_settings import sync_preferences

_LOGGER = logging.getLogger(__name__)
STARTUP_DELAY = 90
_SCHEDULES = {}


class AutomaticSync:
    """Manage one entry's scheduled tasks and shared sync runtime."""

    def __init__(self, hass, entry, runtime):
        self.hass = hass
        self.entry = entry
        self.runtime = runtime
        self._task = None
        self._unsubscribers = []
        self._startup_unsubscribe = None
        self._stopped = False
        self.interval_hours, self.sync_on_startup = (
            sync_preferences(entry)
        )

    async def run_once(self):
        """Refresh meter discovery, then reconcile each registered meter."""
        if self._stopped:
            return
        coordinator = self.hass.data.get(DOMAIN, {}).get(
            self.entry.entry_id
        )
        if coordinator is None:
            return
        try:
            await coordinator.async_refresh()
            if not coordinator.last_update_success:
                raise RuntimeError("Meter discovery refresh failed")
            meters = coordinator.data.get("meters", [])
            _LOGGER.debug(
                "Scheduled Energy Usage discovered meters: %r",
                meters,
            )
            meter_ids = sorted({
                int(m["id"]) for m in meters
                if int(m.get("commodity", -1)) in (1, 7)
            })
        except Exception:
            _LOGGER.exception(
                "Scheduled Energy Usage discovery failed; retry next cycle"
            )
            return
        for meter_id in meter_ids:
            if self._stopped:
                return
            try:
                _LOGGER.debug(
                    "Scheduled Energy Usage BEGIN meter=%d",
                    meter_id,
                )
                result = await sync_one(
                    self.hass, self.entry, meter_id, self.runtime
                )
                _LOGGER.info(
                    "Scheduled Energy Usage meter=%d verified=%d "
                    "added=%d corrected=%d",
                    meter_id, result.observations,
                    result.added, result.corrected,
                )
            except Exception:
                _LOGGER.exception(
                    "Scheduled Energy Usage meter=%d failed; "
                    "retry next cycle", meter_id
                )

    @callback
    def trigger(self, _now=None):
        """Skip overlapping cycles; individual meter operations serialize."""
        _LOGGER.debug(
            "Energy Usage scheduler triggered: entry=%s",
            self.entry.entry_id,
        )
        if self._stopped:
            return
        if self._task is not None and not self._task.done():
            _LOGGER.debug("Scheduled Energy Usage cycle already running")
            return
        self._task = self.hass.async_create_task(self.run_once())

    def start(self):
        """Schedule the user-selected cycle and optional startup run."""
        _LOGGER.info(
            "Energy Usage scheduler started: interval=%dh "
            "startup=%s",
            self.interval_hours,
            self.sync_on_startup,
        )
        self._unsubscribers.append(
            async_track_time_interval(
                self.hass, self.trigger,
                timedelta(hours=self.interval_hours)
            )
        )

        @callback
        def on_started(_event=None):
            # A one-shot listener is already removed when invoked.
            self._startup_unsubscribe = None
            if self._stopped:
                return
            _LOGGER.debug(
                "Energy Usage startup timer registered: delay=%ds",
                STARTUP_DELAY,
            )
            self._unsubscribers.append(
                async_call_later(
                    self.hass, STARTUP_DELAY, self.trigger
                )
            )

        if self.sync_on_startup:
            if self.hass.is_running:
                on_started()
            else:
                self._startup_unsubscribe = (
                    self.hass.bus.async_listen_once(
                        EVENT_HOMEASSISTANT_STARTED, on_started
                    )
                )

    async def stop(self):
        """Stop new cycles and let admitted Recorder work finish."""
        self._stopped = True
        if self._startup_unsubscribe is not None:
            self._startup_unsubscribe()
            self._startup_unsubscribe = None
        for unsubscribe in self._unsubscribers:
            unsubscribe()
        self._unsubscribers.clear()
        if self._task is not None:
            await self._task


def start_automatic_sync(hass, entry, runtime):
    """Start only one scheduler for a configured entry."""
    if entry.entry_id in _SCHEDULES:
        return
    schedule = AutomaticSync(hass, entry, runtime)
    schedule.start()
    _SCHEDULES[entry.entry_id] = schedule


async def stop_automatic_sync(entry):
    """Stop only this entry's scheduler."""
    schedule = _SCHEDULES.pop(entry.entry_id, None)
    if schedule is not None:
        await schedule.stop()
