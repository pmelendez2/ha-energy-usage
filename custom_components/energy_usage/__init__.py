# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Project Contributors
"""Energy Usage Home Assistant integration."""

from datetime import timedelta
import logging

from homeassistant.const import CONF_URL, Platform
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator, UpdateFailed,
)

from .api import EnergyApi, EnergyApiError, EnergyAuthError
from .const import CONF_TOKEN, DOMAIN

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass, entry):
    """Set up read-only physical-meter discovery."""
    api = EnergyApi(
        async_get_clientsession(hass),
        entry.data[CONF_URL], entry.data[CONF_TOKEN],
    )

    async def update():
        try:
            meters = await api.meters()
            return {"meters": meters}
        except EnergyAuthError as exc:
            raise ConfigEntryAuthFailed("Energy Ingest token rejected") from exc
        except (EnergyApiError, KeyError, ValueError) as exc:
            raise UpdateFailed("Unable to fetch Energy Ingest data") from exc

    coordinator = DataUpdateCoordinator(
        hass,
        logger=logging.getLogger(__name__),
        name="Energy Usage",
        update_method=update,
        update_interval=timedelta(hours=6),
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    try:
        await hass.config_entries.async_forward_entry_setups(
            entry, PLATFORMS
        )
    except Exception:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        raise
    return True


async def async_unload_entry(hass, entry):
    """Remove the integration without altering Energy Ingest data."""
    unloaded = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )
    if unloaded:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unloaded
