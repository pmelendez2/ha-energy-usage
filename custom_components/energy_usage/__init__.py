# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Project Contributors
"""Energy Usage Home Assistant integration."""

from datetime import timedelta
import logging
from pathlib import Path

from homeassistant.const import CONF_URL, Platform
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator, UpdateFailed,
)
from homeassistant.components.http import StaticPathConfig
from homeassistant.helpers import config_validation as cv

from .api import EnergyApi, EnergyApiError, EnergyAuthError
from .const import CONF_TOKEN, DOMAIN

PLATFORMS = [Platform.SENSOR, Platform.BUTTON]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

EXPLORER_URL = "/energy_usage/energy-usage-explorer.js"

async def async_register_explorer(hass):
    """Register the bundled Energy Usage Explorer resource."""
    explorer_path = (
        Path(__file__).resolve().parent
        / "www"
        / "energy-usage-explorer.js"
    )

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                EXPLORER_URL,
                str(explorer_path),
                cache_headers=False,
            )
        ]
    )

async def async_setup(hass, config):
    """Set up integration-wide Energy Usage resources."""
    await async_register_explorer(hass)
    return True

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
    if hasattr(hass, "services"):
        from .history_import_service import async_register_history_service

        await async_register_history_service(hass, entry)
        from .statistics_sync_service import (
            async_register_sync_service,
        )
        await async_register_sync_service(hass, entry)
        from .statistics_sync_preflight_service import (
            async_register_preflight_service,
        )
        await async_register_preflight_service(hass, entry)
        from .statistics_sync_service import runtime_for_entry
        from .statistics_sync_schedule import start_automatic_sync
        start_automatic_sync(hass, entry, runtime_for_entry(entry))
        async def reload_on_options_change(hass, changed_entry):
            """Apply changed synchronization options."""
            await hass.config_entries.async_reload(
                changed_entry.entry_id
            )

        entry.async_on_unload(
            entry.add_update_listener(reload_on_options_change)
        )
    return True


async def async_unload_entry(hass, entry):
    """Drain admitted synchronization before unloading platforms."""
    from .statistics_sync_schedule import (
        start_automatic_sync,
        stop_automatic_sync,
    )
    from .statistics_sync_service import (
        existing_runtime_for_entry,
        forget_runtime,
    )

    runtime = existing_runtime_for_entry(entry)
    if runtime is not None:
        runtime.begin_close()
    try:
        await stop_automatic_sync(entry)
        if runtime is not None:
            await runtime.drain()
        unloaded = await hass.config_entries.async_unload_platforms(
            entry, PLATFORMS
        )
    except BaseException:
        if runtime is not None:
            runtime.reopen()
            start_automatic_sync(hass, entry, runtime)
        raise
    if not unloaded:
        if runtime is not None:
            runtime.reopen()
            start_automatic_sync(hass, entry, runtime)
        return False
    if unloaded:
        # Keep the coordinator available until admitted work finishes.
        await forget_runtime(entry)
        from .import_status import clear_entry

        clear_entry(entry.entry_id)
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)

        if not hass.data.get(DOMAIN) and hasattr(hass, "services"):
            from .history_import_service import SERVICE

            hass.services.async_remove(DOMAIN, SERVICE)
            from .statistics_sync_service import (
                SERVICE as SYNC_SERVICE,
            )
            hass.services.async_remove(DOMAIN, SYNC_SERVICE)
            from .statistics_sync_preflight_service import (
                SERVICE as PREFLIGHT_SERVICE,
            )
            hass.services.async_remove(DOMAIN, PREFLIGHT_SERVICE)
    return unloaded
