# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Project Contributors
"""Validate metadata-only discovery without Home Assistant installed."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock


COMPONENT = (
    Path(__file__).resolve().parents[1]
    / "custom_components/energy_usage"
)


class DiscoveryTests(unittest.IsolatedAsyncioTestCase):
    """Ensure diagnostic sensors never imply usage-history readiness."""

    @classmethod
    def setUpClass(cls):
        cls.saved = dict(sys.modules)
        for name in (
            "homeassistant",
            "homeassistant.components",
            "homeassistant.components.sensor",
            "homeassistant.components.recorder",
            "homeassistant.components.recorder.statistics",
            "homeassistant.helpers",
            "homeassistant.helpers.entity",
            "homeassistant.helpers.update_coordinator",
        ):
            module = types.ModuleType(name)
            module.__path__ = []
            sys.modules[name] = module
        sys.modules["homeassistant.components.sensor"].SensorEntity = type(
            "SensorEntity", (), {}
        )
        sys.modules[
            "homeassistant.components.recorder"
        ].get_instance = Mock()
        sys.modules[
            "homeassistant.components.recorder.statistics"
        ].get_last_statistics = Mock()
        sys.modules["homeassistant.helpers.entity"].EntityCategory = (
            types.SimpleNamespace(DIAGNOSTIC="diagnostic")
        )

        class CoordinatorEntity:
            def __init__(self, coordinator):
                self.coordinator = coordinator

        sys.modules[
            "homeassistant.helpers.update_coordinator"
        ].CoordinatorEntity = CoordinatorEntity
        pkg = types.ModuleType("_discovery_test")
        pkg.__path__ = [str(COMPONENT)]
        sys.modules["_discovery_test"] = pkg
        const = types.ModuleType("_discovery_test.const")
        const.DOMAIN = "energy_usage"
        sys.modules["_discovery_test.const"] = const
        spec = importlib.util.spec_from_file_location(
            "_discovery_test.sensor", COMPONENT / "sensor.py"
        )
        cls.module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.module
        spec.loader.exec_module(cls.module)

    @classmethod
    def tearDownClass(cls):
        sys.modules.clear()
        sys.modules.update(cls.saved)

    async def test_one_registration_sensor_per_meter(self):
        coordinator = types.SimpleNamespace(data={
            "meters": [
                {"id": 1, "display_name": "Electric", "commodity": 1},
                {"id": 2, "display_name": "Gas", "commodity": 7},
            ]
        })
        entry = types.SimpleNamespace(entry_id="example-entry")
        ha = types.SimpleNamespace(data={
            "energy_usage": {entry.entry_id: coordinator}
        })
        add = Mock()
        await self.module.async_setup_entry(ha, entry, add)
        sensors = add.call_args.args[0]
        self.assertEqual(len(sensors), 8)
        self.assertEqual(
            [sensor.native_value for sensor in sensors[::4]],
            ["Registered", "Registered"],
        )
        self.assertTrue(all(
            "_registration" in sensor._attr_unique_id
            for sensor in sensors[::4]
        ))
        self.assertTrue(all(
            "_import_status" in sensor._attr_unique_id
            for sensor in sensors[1::4]
        ))
        self.assertTrue(all(
            "_last_attempt" in sensor._attr_unique_id
            for sensor in sensors[2::4]
        ))
        self.assertTrue(all(
            "_last_error" in sensor._attr_unique_id
            for sensor in sensors[3::4]
        ))

    async def test_removed_meter_is_not_registered(self):
        coordinator = types.SimpleNamespace(data={"meters": []})
        meter = {"id": 5, "display_name": "Electric"}
        entry = types.SimpleNamespace(entry_id="example-entry")
        sensor = self.module.MeterRegistrationSensor(
            coordinator, meter, entry
        )
        self.assertIsNone(sensor.native_value)

    async def test_status_reads_recorder_before_reporting_imported(self):
        entry = types.SimpleNamespace(entry_id="example-entry")
        meter = {"id": 1, "display_name": "Electric", "commodity": 1}
        recorder = sys.modules["homeassistant.components.recorder"]
        instance = Mock()

        async def read_history(*args):
            return read_history.rows

        read_history.rows = {}
        instance.async_add_executor_job = read_history
        recorder.get_instance.return_value = instance
        sensor = self.module.HistoryImportStatusSensor(
            object(), entry, meter
        )
        await sensor.async_update()
        self.assertEqual(sensor._attr_native_value, "Not imported")
        read_history.rows = {"energy_usage:electricity_meter_1": [{}]}
        await sensor.async_update()
        self.assertEqual(sensor._attr_native_value, "Imported")

    async def test_last_attempt_and_error_are_device_entities(self):
        entry = types.SimpleNamespace(entry_id="example-entry")
        meter = {"id": 9, "display_name": "Electric", "commodity": 1}
        import_status = sys.modules[
            "_discovery_test.import_status"
        ]
        key = import_status.key_for(entry.entry_id, 9)
        attempt = self.module.LastImportAttemptSensor(entry, meter)
        error = self.module.LastImportErrorSensor(entry, meter)
        await attempt.async_update()
        self.assertEqual(attempt._attr_native_value, "Not attempted")
        self.assertEqual(error._attr_native_value, "None")
        import_status.started(key)
        import_status.failed(key, "History already exists")
        await attempt.async_update()
        await error.async_update()
        self.assertEqual(attempt._attr_native_value, "Failed")
        self.assertEqual(error._attr_native_value, "History already exists")
        import_status.clear_entry(entry.entry_id)


if __name__ == "__main__":
    unittest.main()
