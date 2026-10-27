# SPDX-License-Identifier: MIT
"""Explicit initial import into Home Assistant Recorder.

Never replace existing series or silently modify historical statistics.
"""

from __future__ import annotations
import asyncio
from datetime import date

import logging

import voluptuous as vol
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import (
    StatisticData, StatisticMeanType, StatisticMetaData,
)
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics, get_last_statistics,
)
from homeassistant.const import CONF_URL
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EnergyApi, EnergyApiError
from .const import CONF_TOKEN, DOMAIN
from .date_ranges import selected_calendar_dates_utc
from .history_fetch import fetch_usage_history
from .history import HistoryValidationError
from .history_import_guard import (
    InitialImportBlocked, check_initial_import,
)
from .history_range import complete_history_dates
from .statistics_import import StatisticsImportError, build_statistics

_LOGGER = logging.getLogger(__name__)
SERVICE = "import_historical_usage"
SCHEMA = vol.Schema({
    vol.Required("meter_id"): vol.All(vol.Coerce(int), vol.Range(min=1)),
    vol.Required("start_date"): vol.Date(),
    vol.Required("end_date"): vol.Date(),
    vol.Required("confirm_initial_import"): vol.In([True]),
})
_IMPORT_LOCKS = {}
_QUEUED_IMPORTS = set()


async def async_import_complete_history(hass, entry, meter_id):
    """Discover the full verified range and import it once."""
    meter = _find_meter(hass, entry, meter_id)
    api = EnergyApi(
        async_get_clientsession(hass),
        entry.data[CONF_URL], entry.data[CONF_TOKEN],
    )
    # The stream is read-only and contains all accepted observations.
    try:
        stream = await api.stream(meter_id)
        start, end = complete_history_dates(
            stream, int(meter["commodity"]), hass.config.time_zone
        )
        await _import_range(hass, entry, meter, start, end)
    except (HistoryValidationError, StatisticsImportError,
            InitialImportBlocked, ValueError) as exc:
        raise ServiceValidationError(str(exc)) from exc
    except EnergyApiError as exc:
        raise HomeAssistantError(
            "Cannot read the accepted Energy Ingest history"
        ) from exc


def _find_meter(hass, entry, meter_id):
    if len(hass.data.get(DOMAIN, {})) != 1:
        raise ServiceValidationError(
            "Multiple Energy Usage entries unsupported"
        )
    coordinator = hass.data[DOMAIN][entry.entry_id]
    matches = [
        meter for meter in coordinator.data["meters"]
        if int(meter["id"]) == meter_id
    ]
    if len(matches) != 1:
        raise ServiceValidationError(
            "Meter is not registered in this entry"
        )
    if int(matches[0]["commodity"]) not in (1, 7):
        raise ServiceValidationError("Unsupported meter type")
    return matches[0]


async def _import_range(hass, entry, meter, start_day, end_day):
    """Serialize imports and refuse any existing Recorder series."""
    meter_id = int(meter["id"])
    commodity = int(meter["commodity"])
    if end_day < start_day or (end_day - start_day).days > 440:
        raise ServiceValidationError("Select up to 441 calendar days")
    lock_key = (entry.entry_id, meter_id)
    lock = _IMPORT_LOCKS.setdefault(lock_key, asyncio.Lock())
    async with lock:
        statistic_id = (
            f"{DOMAIN}:{'electricity' if commodity == 1 else 'gas'}"
            f"_meter_{meter_id}"
        )
        last = await get_instance(hass).async_add_executor_job(
            get_last_statistics, hass, 1, statistic_id,
            True, {"sum"}
        )
        try:
            check_initial_import(_QUEUED_IMPORTS, lock_key, bool(last))
        except InitialImportBlocked as exc:
            raise ServiceValidationError(str(exc)) from exc
        api = EnergyApi(
            async_get_clientsession(hass),
            entry.data[CONF_URL], entry.data[CONF_TOKEN],
        )
        begin, stop = selected_calendar_dates_utc(
            start_day, end_day, hass.config.time_zone
        )
        readings = await fetch_usage_history(
            api, meter_id, commodity, begin, stop
        )
        batch = build_statistics(
            meter_id, commodity, meter["display_name"], readings,
            time_zone=hass.config.time_zone,
        )
        metadata = StatisticMetaData(
            has_sum=True,
            mean_type=StatisticMeanType.NONE,
            name=f"{batch.name} usage",
            source=DOMAIN,
            statistic_id=batch.statistic_id,
            unit_class="energy",
            unit_of_measurement=(
                "kWh" if commodity == 1 else "thm"
            ),
        )
        values = [StatisticData(**row) for row in batch.rows]
        async_add_external_statistics(hass, metadata, values)
        # The Recorder API only queues the job; it does not acknowledge
        # persistence. Keep the reservation until read-back confirms rows,
        # or until Home Assistant has restarted and drained its old queue.
        _QUEUED_IMPORTS.add(lock_key)
        _LOGGER.info(
            "Queued %d validated usage readings for meter %d; "
            "%d missing intervals were not filled",
            len(values), meter_id, batch.missing_intervals,
        )


async def async_register_history_service(hass, entry):
    """Register guarded first-import service; never auto-import on startup."""
    if hass.services.has_service(DOMAIN, SERVICE):
        return

    async def import_history(call):
        meter_id = call.data["meter_id"]
        start_day = call.data["start_date"]
        end_day = call.data["end_date"]

        if isinstance(start_day, str):
            start_day = date.fromisoformat(start_day)

        if isinstance(end_day, str):
            end_day = date.fromisoformat(end_day)

        meter = _find_meter(hass, entry, meter_id)
        try:
            await _import_range(hass, entry, meter, start_day, end_day)
        except (HistoryValidationError, StatisticsImportError,
                InitialImportBlocked, ValueError) as exc:
            raise ServiceValidationError(str(exc)) from exc
        except EnergyApiError as exc:
            raise HomeAssistantError(
                "Cannot read the accepted Energy Ingest history"
            ) from exc

    hass.services.async_register(
        DOMAIN, SERVICE, import_history, schema=SCHEMA
    )
