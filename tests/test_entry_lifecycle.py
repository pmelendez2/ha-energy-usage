# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Project Contributors
"""Exercise setup, authentication recovery, and unload with HA doubles."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import AsyncMock, Mock


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/energy_usage"


class _Coordinator:
    """Minimal coordinator, refreshing through the supplied callback."""

    def __init__(self, ha, *, update_method, **kwargs):
        self.update_method = update_method
        self.data = None

    async def async_config_entry_first_refresh(self):
        self.data = await self.update_method()


class _Entry:
    """Config-entry substitute."""

    entry_id = "integration-one"

    def __init__(
        self,
        url: str = "http://example.test:8080",
        api_token: str = "test-api-token",
    ) -> None:
        """Configure the simulated Energy Ingest connection."""
        self.data = {"url": url, "api_token": api_token}


class LifecycleTests(unittest.IsolatedAsyncioTestCase):
    """Test the HA setup boundary without installing HA Core."""

    @classmethod
    def setUpClass(cls):
        cls.saved = dict(sys.modules)
        ha = types.ModuleType("homeassistant")
        ha.__path__ = []
        components = types.ModuleType("homeassistant.components")
        components.__path__ = []

        http = types.ModuleType("homeassistant.components.http")
        http.StaticPathConfig = Mock()
        validation = types.ModuleType(
            "homeassistant.helpers.config_validation"
        )
        validation.config_entry_only_config_schema = Mock(
            return_value=Mock()
        )
        const = types.ModuleType("homeassistant.const")
        const.CONF_URL = "url"
        const.Platform = types.SimpleNamespace(SENSOR="sensor")
        exceptions = types.ModuleType("homeassistant.exceptions")
        exceptions.ConfigEntryAuthFailed = type(
            "ConfigEntryAuthFailed", (Exception,), {}
        )
        client = types.ModuleType("homeassistant.helpers.aiohttp_client")
        client.async_get_clientsession = lambda ha: object()
        coordinator = types.ModuleType(
            "homeassistant.helpers.update_coordinator"
        )
        coordinator.DataUpdateCoordinator = _Coordinator
        coordinator.UpdateFailed = type("UpdateFailed", (Exception,), {})
        for name, module in {
            "homeassistant": ha,
            "homeassistant.components": components,
            "homeassistant.components.http": http,
            "homeassistant.const": const,
            "homeassistant.exceptions": exceptions,
            "homeassistant.helpers": types.ModuleType(
                "homeassistant.helpers"
            ),
            "homeassistant.helpers.config_validation": validation,
            "homeassistant.helpers.aiohttp_client": client,
            "homeassistant.helpers.update_coordinator": coordinator,
        }.items():
            sys.modules[name] = module
        pkg = types.ModuleType("_energy_test")
        pkg.__path__ = [str(COMPONENT)]
        sys.modules["_energy_test"] = pkg
        api = types.ModuleType("_energy_test.api")
        api.EnergyApiError = type("EnergyApiError", (Exception,), {})
        api.EnergyAuthError = type("EnergyAuthError", (api.EnergyApiError,), {})
        api.EnergyApi = Mock()
        sys.modules["_energy_test.api"] = api
        constants = types.ModuleType("_energy_test.const")
        constants.CONF_TOKEN = "api_token"
        constants.DOMAIN = "energy_usage"
        sys.modules["_energy_test.const"] = constants
        spec = importlib.util.spec_from_file_location(
            "_energy_test", COMPONENT / "__init__.py"
        )
        cls.module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.module
        spec.loader.exec_module(cls.module)
        cls.api = api
        cls.exc = exceptions

    @classmethod
    def tearDownClass(cls):
        sys.modules.clear()
        sys.modules.update(cls.saved)

    def setUp(self):
        self.entry = _Entry()
        self.ha = types.SimpleNamespace(
            data={},
            config_entries=types.SimpleNamespace(
                async_forward_entry_setups=AsyncMock(),
                async_unload_platforms=AsyncMock(return_value=True),
            ),
        )
        self.instance = Mock()
        self.instance.meters = AsyncMock(return_value=[{"id": 7}])
        self.instance.stream = AsyncMock(
            return_value={"resolved": True, "intervals": []}
        )
        self.api.EnergyApi.return_value = self.instance

    async def test_first_refresh_and_unload(self):
        self.assertTrue(await self.module.async_setup_entry(
            self.ha, self.entry
        ))
        data = self.ha.data["energy_usage"][self.entry.entry_id].data
        self.assertEqual(data["meters"], [{"id": 7}])
        self.assertNotIn("streams", data)
        self.instance.stream.assert_not_awaited()
        self.ha.config_entries.async_forward_entry_setups.assert_awaited_once()
        self.assertTrue(await self.module.async_unload_entry(
            self.ha, self.entry
        ))
        self.assertNotIn(self.entry.entry_id, self.ha.data["energy_usage"])

    async def test_auth_error_requests_reauthentication(self):
        self.instance.meters.side_effect = self.api.EnergyAuthError("bad")
        with self.assertRaises(self.exc.ConfigEntryAuthFailed):
            await self.module.async_setup_entry(self.ha, self.entry)

    async def test_api_error_propagates_to_coordinator(self):
        self.instance.meters.side_effect = self.api.EnergyApiError("down")
        with self.assertRaises(self.module.UpdateFailed):
            await self.module.async_setup_entry(self.ha, self.entry)

    async def test_forwarding_failure_removes_partial_state(self):
        self.ha.config_entries.async_forward_entry_setups.side_effect = (
            RuntimeError("forward failed")
        )
        with self.assertRaises(RuntimeError):
            await self.module.async_setup_entry(self.ha, self.entry)
        self.assertNotIn(
            self.entry.entry_id, self.ha.data["energy_usage"]
        )

    async def test_unload_failure_keeps_state(self):
        await self.module.async_setup_entry(self.ha, self.entry)
        self.ha.config_entries.async_unload_platforms.return_value = False
        self.assertFalse(await self.module.async_unload_entry(
            self.ha, self.entry
        ))
        self.assertIn(self.entry.entry_id, self.ha.data["energy_usage"])


if __name__ == "__main__":
    unittest.main()
