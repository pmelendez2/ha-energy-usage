# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Exercise ADR-0003 persistence and conflict paths without HA or MariaDB."""

import ast
from pathlib import Path
from types import SimpleNamespace
import asyncio
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "custom_components/energy_usage/utility_upload.py"


class ApiFailure(Exception):
    pass


class MemoryStore:
    data = None

    def __init__(self, *_args):
        pass

    async def async_load(self):
        return MemoryStore.data

    async def async_save(self, data):
        MemoryStore.data = {key: list(value) for key, value in data.items()}


class ResponseView:
    def json(self, data, status_code=200):
        return status_code, data


class Backend:
    def __init__(self):
        self.associations = {13: None, 14: 2}
        self.calls = []

    async def resource_association(self, resource_id):
        if resource_id not in self.associations:
            raise ApiFailure("resource not found")
        meter = self.associations[resource_id]
        return {
            "resource_id": resource_id,
            "physical_meter_id": meter,
            "status": "associated" if meter else "unassociated",
        }

    async def associate_resource(self, meter_id, resource_id):
        self.calls.append((meter_id, resource_id))
        if self.associations[resource_id] not in (None, meter_id):
            raise ApiFailure("conflict")
        self.associations[resource_id] = meter_id
        return {"resource_id": resource_id, "meter_id": meter_id,
                "status": "associated"}


def load_view():
    tree = ast.parse(SOURCE.read_text())
    view = next(node for node in tree.body
                if isinstance(node, ast.ClassDef)
                and node.name == "UtilityUploadView")
    namespace = {
        "HomeAssistantView": ResponseView,
        "Store": MemoryStore,
        "asyncio": asyncio,
        "DOMAIN": "energy_usage",
        "EnergyApiError": ApiFailure,
        "_LOGGER": SimpleNamespace(warning=lambda *_: None,
                                    exception=lambda *_: None),
        "web": SimpleNamespace(
            HTTPBadRequest=ValueError,
            HTTPBadGateway=ApiFailure,
            HTTPConflict=ValueError,
            HTTPForbidden=ValueError,
        ),
    }
    exec(compile(ast.Module(body=[view], type_ignores=[]),
                 str(SOURCE), "exec"), namespace)
    return namespace["UtilityUploadView"]


class RecoveryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        MemoryStore.data = None
        self.backend = Backend()
        self.entry = SimpleNamespace(entry_id="entry-1")
        coordinator = SimpleNamespace(data={"meters": [
            {"id": 1, "commodity": 1},
            {"id": 2, "commodity": 7},
        ]})
        self.hass = SimpleNamespace(data={"energy_usage": {
            "entry-1": coordinator,
        }})
        self.View = load_view()
        self.view = self.View(self.hass)
        self.view._api = lambda _entry: self.backend
        self.synced = []

        async def sync(_entry, meter_ids):
            self.synced.extend(meter_ids)
            return sorted(set(meter_ids))

        self.view._sync = sync

    async def test_restart_recovers_pending_without_xml(self):
        await self.view._remember(self.entry, [13, 14])
        restarted = self.View(self.hass)
        restarted._api = lambda _entry: self.backend
        await restarted._load_pending()
        self.assertEqual(restarted._pending["entry-1"], [13, 14])
        states = await restarted._lookup(self.entry, [13, 14])
        self.assertEqual(states[0]["status"], "unassociated")
        self.assertEqual(states[1]["physical_meter_id"], 2)

    async def test_confirmed_mapping_is_reused_and_verified(self):
        await self.view._remember(self.entry, [14])
        code, result = await self.view._associate(self.entry, {
            "associations": [{"resource_id": 14, "meter_id": 2}],
        })
        self.assertEqual(code, 200)
        self.assertTrue(result["synchronized"])
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.synced, [2])
        self.assertEqual(MemoryStore.data["entry-1"], [])

    async def test_conflict_prevents_mutation_and_recorder(self):
        await self.view._remember(self.entry, [14])
        code, result = await self.view._associate(self.entry, {
            "associations": [{"resource_id": 14, "meter_id": 1}],
        })
        self.assertEqual(code, 409)
        self.assertEqual(result["conflicting_resource_ids"], [14])
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.synced, [])
        self.assertEqual(MemoryStore.data["entry-1"], [14])

    async def test_recorder_failure_leaves_import_retryable(self):
        await self.view._remember(self.entry, [13])

        async def fail(*_args):
            raise RuntimeError("Recorder unavailable")

        self.view._sync = fail
        code, result = await self.view._associate(self.entry, {
            "associations": [{"resource_id": 13, "meter_id": 1}],
        })
        self.assertEqual(code, 207)
        self.assertFalse(result["synchronized"])
        self.assertEqual(MemoryStore.data["entry-1"], [13])
        self.assertEqual(self.backend.associations[13], 1)


if __name__ == "__main__":
    unittest.main()
