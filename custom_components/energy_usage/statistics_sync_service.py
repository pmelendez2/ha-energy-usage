# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Explicit Energy Usage synchronization action for existing HA entries.

The action succeeds only after Recorder read-back matches canonical data.
"""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.const import CONF_URL
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EnergyApi, EnergyApiError
from .const import CONF_TOKEN, DOMAIN
from .statistics_sync_plan import StatisticsSyncError
from .statistics_sync_runtime import MeterSyncRuntime

_LOGGER = logging.getLogger(__name__)
SERVICE = "sync_usage"
_RUNTIMES = {}


def runtime_for_entry(entry):
    '''Reuse one lock manager for manual and scheduled synchronization.'''
    return _RUNTIMES.setdefault(entry.entry_id, MeterSyncRuntime())


def existing_runtime_for_entry(entry):
    """Look up a runtime without creating another one."""
    return _RUNTIMES.get(entry.entry_id)


async def forget_runtime(entry):
    """Drain admitted work before releasing the shared lock manager."""
    runtime = _RUNTIMES.get(entry.entry_id)
    if runtime is not None:
        await runtime.drain()
        if _RUNTIMES.get(entry.entry_id) is runtime:
            _RUNTIMES.pop(entry.entry_id, None)

SCHEMA = vol.Schema({vol.Required("meter_id"): vol.All(vol.Coerce(int), vol.Range(min=1))})


def find_meter(hass, entry, meter_id):
    """Require the selected meter to belong to this single config entry."""
    entries = hass.data.get(DOMAIN, {})
    if len(entries) != 1 or entry.entry_id not in entries:
        raise ServiceValidationError("Exactly one Energy Usage entry required")
    coordinator = entries[entry.entry_id]
    meters = coordinator.data.get("meters", [])
    matches = [
        meter for meter in meters
        if int(meter.get("id", -1)) == meter_id
    ]
    if len(matches) != 1:
        raise ServiceValidationError("Meter not registered with this entry")
    if int(matches[0].get("commodity", -1)) not in (1, 7):
        raise ServiceValidationError("Unsupported energy commodity")
    return matches[0]


async def sync_one(hass, entry, meter_id, runtime):
    """Queue safe reconciliation from the complete authoritative stream."""
    meter = find_meter(hass, entry, meter_id)
    api = EnergyApi(
        async_get_clientsession(hass),
        entry.data[CONF_URL], entry.data[CONF_TOKEN],
    )
    try:
        result = await runtime.sync_meter(
            hass, api, meter, confirmed=True
        )
    except StatisticsSyncError as exc:
        raise ServiceValidationError(str(exc)) from exc
    except EnergyApiError as exc:
        raise HomeAssistantError(
            "Unable to retrieve verified Energy Ingest history"
        ) from exc
    _LOGGER.info(
        "Meter %d synchronization persisted and verified: "
        "%d added, %d corrected, %d unchanged; %d observations",
        result.meter_id, result.added,
        result.corrected, result.unchanged, result.observations,
    )
    return result


async def async_register_sync_service(hass, entry):
    """Register the manual synchronization service."""
    if hass.services.has_service(DOMAIN, SERVICE):
        return
    runtime = runtime_for_entry(entry)

    async def handle(call):
        meter_id = int(call.data["meter_id"])
        await sync_one(hass, entry, meter_id, runtime)

    hass.services.async_register(
        DOMAIN, SERVICE, handle, schema=SCHEMA
    )
