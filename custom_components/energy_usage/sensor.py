# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Project Contributors
"""Read-only physical-meter registration diagnostics.

A registered meter does not imply that its readings are resolved or
ready for Home Assistant Energy Dashboard ingestion.
"""

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(ha, entry, async_add_entities):
    """Create a diagnostic entity for each discovered physical meter."""
    coordinator = ha.data[DOMAIN][entry.entry_id]
    entities = [
        MeterRegistrationSensor(coordinator, meter, entry)
        for meter in coordinator.data["meters"]
    ]
    async_add_entities(entities)


class MeterRegistrationSensor(CoordinatorEntity, SensorEntity):
    """Indicate that Energy Ingest reports a registered meter."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:counter"

    def __init__(self, coordinator, meter, entry):
        """Keep meter identity stable within the config entry."""
        super().__init__(coordinator)
        self._meter_id = int(meter["id"])
        self._entry_id = entry.entry_id
        self._meter_name = str(meter["display_name"])
        self._attr_name = f"{self._meter_name} registration"
        self._attr_unique_id = (
            f"{DOMAIN}_{self._entry_id}_{self._meter_id}_registration"
        )
        self._attr_device_info = {
            "identifiers": {
                (DOMAIN, f"{self._entry_id}:{self._meter_id}")
            },
            "name": self._meter_name,
            "manufacturer": "Energy Ingest",
            "model": "Physical energy meter",
        }

    @property
    def native_value(self):
        """Report registration only; never infer history readiness."""
        meters = self.coordinator.data.get("meters", [])
        return (
            "Registered"
            if any(int(meter["id"]) == self._meter_id
                   for meter in meters)
            else None
        )
