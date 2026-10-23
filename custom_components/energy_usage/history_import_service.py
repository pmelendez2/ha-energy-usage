# SPDX-License-Identifier: MIT
"""Explicit initial import into Home Assistant Recorder.

Never replace existing series or silently modify historical statistics.
"""

from __future__ import annotations
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
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EnergyApi
from .const import CONF_TOKEN, DOMAIN
from .date_ranges import selected_calendar_dates_utc
from .history_fetch import fetch_usage_history
from .statistics_import import build_statistics

_LOGGER = logging.getLogger(__name__)
SERVICE = "import_historical_usage"
SCHEMA = vol.Schema({
    vol.Required("meter_id"): vol.All(vol.Coerce(int), vol.Range(min=1)),
    vol.Required("start_date"): vol.Date(),
    vol.Required("end_date"): vol.Date(),
    vol.Required("confirm_initial_import"): vol.In([True]),
})


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

        if (end_day < start_day
                or (end_day - start_day).days > 440):
            raise ValueError("Select up to 441 calendar days")
        if len(hass.data.get(DOMAIN, {})) != 1:
            raise ValueError("Multiple Energy Usage entries unsupported")
        coordinator = hass.data[DOMAIN][entry.entry_id]
        matches = [m for m in coordinator.data["meters"]
                   if int(m["id"]) == meter_id]
        if len(matches) != 1:
            raise ValueError("Meter is not registered in this entry")
        meter = matches[0]
        commodity = int(meter["commodity"])
        if commodity not in (1, 7):
            raise ValueError("Unsupported meter type")
        api = EnergyApi(
            async_get_clientsession(hass),
            entry.data[CONF_URL], entry.data[CONF_TOKEN]
        )
        begin, stop = selected_calendar_dates_utc(
            start_day, end_day, hass.config.time_zone
        )
        # All API reads must succeed before touching Recorder.
        readings = await fetch_usage_history(
            api, meter_id, commodity, begin, stop
        )
        batch = build_statistics(
            meter_id, commodity, meter["display_name"], readings,
            time_zone=hass.config.time_zone,
        )
        last = await get_instance(hass).async_add_executor_job(
            get_last_statistics, hass, 1, batch.statistic_id,
            True, {"sum"}
        )
        if last:
            raise ValueError(
                "History already exists. Correction-safe sync is required"
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
        # HA's supported external statistics API; not a direct DB write.
        async_add_external_statistics(hass, metadata, values)
        _LOGGER.info(
            "Queued %d validated usage readings for meter %d; "
            "%d missing intervals were not filled",
            len(values), meter_id, batch.missing_intervals,
        )

    hass.services.async_register(
        DOMAIN, SERVICE, import_history, schema=SCHEMA
    )
