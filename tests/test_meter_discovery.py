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
                {"id": 1, "display_name": "Electric"},
                {"id": 2, "display_name": "Gas"},
            ]
        })
        entry = types.SimpleNamespace(entry_id="example-entry")
        ha = types.SimpleNamespace(data={
            "energy_usage": {entry.entry_id: coordinator}
        })
        add = Mock()
        await self.module.async_setup_entry(ha, entry, add)
        sensors = add.call_args.args[0]
        self.assertEqual(len(sensors), 2)
        self.assertEqual(
            [sensor.native_value for sensor in sensors],
            ["Registered", "Registered"],
        )
        self.assertTrue(all(
            "_registration" in sensor._attr_unique_id
            for sensor in sensors
        ))

    async def test_removed_meter_is_not_registered(self):
        coordinator = types.SimpleNamespace(data={"meters": []})
        meter = {"id": 5, "display_name": "Electric"}
        entry = types.SimpleNamespace(entry_id="example-entry")
        sensor = self.module.MeterRegistrationSensor(
            coordinator, meter, entry
        )
        self.assertIsNone(sensor.native_value)


if __name__ == "__main__":
    unittest.main()
