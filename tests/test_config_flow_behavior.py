# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Project Contributors
"""Exercise Energy Usage configuration steps without HA installation."""

import asyncio
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import AsyncMock


COMPONENT = (Path(__file__).resolve().parents[1] /
             "custom_components/energy_usage")


class _Required:
    """Small stand-in for a required schema key."""

    def __init__(self, key, default=None):
        self.key = key
        self.default = default


class _Flow:
    """Emulate the native Home Assistant config-flow return values."""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()

    async def async_set_unique_id(self, value):
        self.unique_id = value

    def _abort_if_unique_id_configured(self):
        if getattr(self, "duplicate", False):
            raise RuntimeError("duplicate")

    def _abort_if_unique_id_mismatch(self):
        if self.unique_id != self._get_reconfigure_entry().unique_id:
            raise RuntimeError("server identity mismatch")

    def async_show_form(self, **kwargs):
        return {"type": "form", **kwargs}

    def async_create_entry(self, **kwargs):
        return {"type": "create_entry", **kwargs}

    def async_update_reload_and_abort(self, entry, **kwargs):
        return {"type": "update", "entry": entry, **kwargs}

    def _get_reauth_entry(self):
        return self.entry

    def _get_reconfigure_entry(self):
        return self.entry


class ConfigFlowTests(unittest.IsolatedAsyncioTestCase):
    """Verify actual user, reauth, and reconfigure paths."""

    @classmethod
    def setUpClass(cls):
        cls.saved = dict(sys.modules)
        vol = types.ModuleType("voluptuous")
        vol.Required = _Required
        vol.Schema = lambda value: value
        sys.modules["voluptuous"] = vol
        ha = types.ModuleType("homeassistant")
        ha.__path__ = []
        cfg = types.ModuleType("homeassistant.config_entries")
        cfg.ConfigFlow = _Flow
        const = types.ModuleType("homeassistant.const")
        const.CONF_URL = "url"
        client = types.ModuleType("homeassistant.helpers.aiohttp_client")
        client.async_get_clientsession = lambda ha: object()
        for name, module in {
            "homeassistant": ha,
            "homeassistant.config_entries": cfg,
            "homeassistant.const": const,
            "homeassistant.helpers": types.ModuleType("homeassistant.helpers"),
            "homeassistant.helpers.aiohttp_client": client,
        }.items():
            sys.modules[name] = module
        pkg = types.ModuleType("_energy_flow_test")
        pkg.__path__ = [str(COMPONENT)]
        sys.modules[pkg.__name__] = pkg
        api = types.ModuleType("_energy_flow_test.api")
        api.EnergyApiError = type("EnergyApiError", (Exception,), {})
        api.EnergyAuthError = type("EnergyAuthError", (api.EnergyApiError,), {})
        api.EnergyApi = lambda *args: None
        sys.modules[api.__name__] = api
        settings = types.ModuleType("_energy_flow_test.const")
        settings.CONF_TOKEN = "api_token"
        settings.DEFAULT_URL = "http://127.0.0.1:8080"
        settings.DOMAIN = "energy_usage"
        sys.modules[settings.__name__] = settings
        spec = importlib.util.spec_from_file_location(
            "_energy_flow_test.config_flow", COMPONENT / "config_flow.py"
        )
        cls.module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.module
        spec.loader.exec_module(cls.module)
        cls.api = api

    @classmethod
    def tearDownClass(cls):
        sys.modules.clear()
        sys.modules.update(cls.saved)

    def setUp(self):
        self.flow = self.module.EnergyUsageConfigFlow()
        self.flow.ha = object()
        self.flow._validate = AsyncMock(return_value=[{"id": 7}])
        self.flow.entry = types.SimpleNamespace(
            data={"url": "http://example.test:8080",
                  "api_token": "test-api-token"},
            unique_id="http://example.test:8080",
        )

    async def test_user_success(self):
        result = await self.flow.async_step_user({
            "url": "http://example.test:8080/",
            "api_token": "test-api-token",
        })
        self.assertEqual(result["type"], "create_entry")
        self.assertEqual(result["data"]["url"],
                         "http://example.test:8080")
        self.flow._validate.assert_awaited_once()

    async def test_user_invalid_auth(self):
        self.flow._validate.side_effect = self.api.EnergyAuthError()
        result = await self.flow.async_step_user({
            "url": "http://example.test:8080",
            "api_token": "bad-test-token",
        })
        self.assertEqual(result["errors"]["base"], "invalid_auth")

    async def test_user_unavailable(self):
        self.flow._validate.side_effect = self.api.EnergyApiError()
        result = await self.flow.async_step_user({
            "url": "http://example.test:8080",
            "api_token": "test-api-token",
        })
        self.assertEqual(result["errors"]["base"], "cannot_connect")

    async def test_reauth_updates_token_not_database(self):
        result = await self.flow.async_step_reauth_confirm({
            "api_token": "new-test-token",
        })
        self.assertEqual(result["data_updates"],
                         {"api_token": "new-test-token"})
        self.flow._validate.assert_awaited_once_with(
            "http://example.test:8080", "new-test-token"
        )

    async def test_reconfigure_same_server(self):
        result = await self.flow.async_step_reconfigure({
            "url": "http://example.test:8080/",
        })
        self.assertEqual(result["type"], "update")
        self.assertEqual(result["data_updates"],
                         {"url": "http://example.test:8080"})

    async def test_reconfigure_rejects_different_identity(self):
        with self.assertRaisesRegex(RuntimeError, "identity mismatch"):
            await self.flow.async_step_reconfigure({
                "url": "http://192.0.2.10:8080",
            })

    async def test_empty_input_shows_forms(self):
        self.assertEqual((await self.flow.async_step_user())["type"],
                         "form")
        self.assertEqual((await self.flow.async_step_reauth_confirm())[
            "step_id"], "reauth_confirm")
        self.assertEqual((await self.flow.async_step_reconfigure())[
            "step_id"], "reconfigure")


if __name__ == "__main__":
    unittest.main()
