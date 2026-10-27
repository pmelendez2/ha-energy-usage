# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""One-click, guarded import of each meter's complete known history."""

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .history_import_service import async_import_complete_history


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        ImportHistoryButton(hass, entry, meter)
        for meter in coordinator.data["meters"]
        if int(meter["commodity"]) in (1, 7)
    ])


class ImportHistoryButton(ButtonEntity):
    """Import every accepted observation once, with no date input."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:database-import"

    def __init__(self, hass, entry, meter):
        self._hass = hass
        self._entry = entry
        self._meter_id = int(meter["id"])
        name = str(meter["display_name"])
        self._attr_name = f"{name} import complete history (once)"
        self._attr_unique_id = (
            f"{DOMAIN}_{entry.entry_id}_{self._meter_id}_import"
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{entry.entry_id}:{self._meter_id}")},
            "name": name,
            "manufacturer": "Energy Ingest",
            "model": "Physical energy meter",
        }

    async def async_press(self):
        await async_import_complete_history(
            self._hass, self._entry, self._meter_id
        )
