# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Read-only Home Assistant action to inspect canonical/Recorder differences."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.const import CONF_URL
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EnergyApi, EnergyApiError
from .const import CONF_TOKEN, DOMAIN
from .statistics_sync_plan import StatisticsSyncError
from .statistics_sync_preflight import assess_meter
from .statistics_sync_service import find_meter

_LOGGER = logging.getLogger(__name__)
SERVICE = "sync_preflight"
SCHEMA = vol.Schema({
    vol.Required("meter_id"): vol.All(vol.Coerce(int), vol.Range(min=1)),
})


async def preflight_one(hass, entry, meter_id):
    """Assess a meter without calling any Recorder write API."""
    meter = find_meter(hass, entry, meter_id)
    api = EnergyApi(
        async_get_clientsession(hass),
        entry.data[CONF_URL],
        entry.data[CONF_TOKEN],
    )
    try:
        result = await assess_meter(hass, api, meter)
    except StatisticsSyncError as exc:
        raise ServiceValidationError(str(exc)) from exc
    except EnergyApiError as exc:
        raise HomeAssistantError(
            "Unable to retrieve verified Energy Ingest history"
        ) from exc
    _LOGGER.warning(
        "READ-ONLY Energy Usage preflight meter=%d statistic=%s "
        "existing=%d canonical=%d added=%d corrected=%d "
        "unchanged=%d first_changed=%s; NO RECORDER WRITES",
        result.meter_id,
        result.statistic_id,
        result.existing,
        result.canonical,
        result.added,
        result.corrected,
        result.unchanged,
        result.first_changed,
    )
    return result


async def async_register_preflight_service(hass, entry):
    """Expose preflight as an explicit, non-writing action only."""
    if hass.services.has_service(DOMAIN, SERVICE):
        return

    async def handle(call):
        await preflight_one(hass, entry, int(call.data["meter_id"]))

    hass.services.async_register(
        DOMAIN, SERVICE, handle, schema=SCHEMA
    )
