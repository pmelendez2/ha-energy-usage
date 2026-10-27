# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Project Contributors
"""Read-only physical-meter registration diagnostics.

A registered meter does not imply that its readings are resolved or
ready for Home Assistant Energy Dashboard ingestion.
"""

from datetime import timedelta

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import (
    get_last_statistics,
)
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .import_status import attempt_details, key_for, snapshot

SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(ha, entry, async_add_entities):
    """Create a diagnostic entity for each discovered physical meter."""
    coordinator = ha.data[DOMAIN][entry.entry_id]
    entities = []
    for meter in coordinator.data["meters"]:
        entities.append(MeterRegistrationSensor(coordinator, meter, entry))
        if int(meter["commodity"]) in (1, 7):
            entities.append(HistoryImportStatusSensor(ha, entry, meter))
            entities.append(LastImportAttemptSensor(entry, meter))
            entities.append(LastImportErrorSensor(entry, meter))
    async_add_entities(entities, update_before_add=True)


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


class HistoryImportStatusSensor(SensorEntity):
    """Read Recorder to distinguish queued work from durable history."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:database-check"

    def __init__(self, hass, entry, meter):
        self._hass = hass
        meter_id = int(meter["id"])
        name = str(meter["display_name"])
        commodity = int(meter["commodity"])
        self._key = key_for(entry.entry_id, meter_id)
        kind = "electricity" if commodity == 1 else "gas"
        self._statistic_id = f"{DOMAIN}:{kind}_meter_{meter_id}"
        self._attr_name = f"{name} historical import status"
        self._attr_unique_id = (
            f"{DOMAIN}_{entry.entry_id}_{meter_id}_import_status"
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{entry.entry_id}:{meter_id}")},
            "name": name,
            "manufacturer": "Energy Ingest",
            "model": "Physical energy meter",
        }
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}

    async def async_update(self):
        """Check persisted statistics; no write or import is performed."""
        try:
            last = await get_instance(self._hass).async_add_executor_job(
                get_last_statistics, self._hass, 1,
                self._statistic_id, True, {"sum"}
            )
        except Exception:
            # Database read failures are unknown, never "not imported".
            self._attr_native_value = None
            self._attr_available = False
            return
        self._attr_available = True
        state, attempt = snapshot(self._key, bool(last))
        self._attr_native_value = state
        self._attr_extra_state_attributes = attempt


class _LastImportDetailSensor(SensorEntity):
    """Expose in-session attempt details on the meter device page."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _detail_key = None
    _empty_text = None

    def __init__(self, entry, meter):
        meter_id = int(meter["id"])
        name = str(meter["display_name"])
        self._key = key_for(entry.entry_id, meter_id)
        self._attr_name = f"{name} {self._detail_label}"
        self._attr_unique_id = (
            f"{DOMAIN}_{entry.entry_id}_{meter_id}_{self._detail_key}"
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{entry.entry_id}:{meter_id}")},
            "name": name,
            "manufacturer": "Energy Ingest",
            "model": "Physical energy meter",
        }
        self._attr_native_value = self._empty_text

    async def async_update(self):
        """Read the last action without running or retrying an import."""
        detail = attempt_details(self._key)
        self._attr_native_value = (
            detail.get(self._detail_key) or self._empty_text
        )
        self._attr_extra_state_attributes = {
            "last_attempt_at": detail.get("last_attempt_at"),
        }


class LastImportAttemptSensor(_LastImportDetailSensor):
    """Show whether the latest button or service request succeeded."""

    _attr_icon = "mdi:history"
    _detail_key = "last_attempt"
    _detail_label = "last import attempt"
    _empty_text = "Not attempted"


class LastImportErrorSensor(_LastImportDetailSensor):
    """Show the latest import error without hiding imported history."""

    _attr_icon = "mdi:alert-circle-outline"
    _detail_key = "last_error"
    _detail_label = "last import error"
    _empty_text = "None"
