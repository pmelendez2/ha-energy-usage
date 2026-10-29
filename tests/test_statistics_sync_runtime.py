# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Tests for the guarded runtime integration boundary."""

import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch
import sys

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "energy_usage"

# Load the pure runtime module without requiring HA at import time.
PACKAGE = "custom_components.energy_usage"
if PACKAGE not in sys.modules:
    import types
    parent = types.ModuleType("custom_components")
    parent.__path__ = [str(ROOT / "custom_components")]
    sys.modules.setdefault("custom_components", parent)
    pkg = types.ModuleType(PACKAGE)
    pkg.__path__ = [str(COMPONENT)]
    sys.modules[PACKAGE] = pkg

spec = importlib.util.spec_from_file_location(
    f"{PACKAGE}.statistics_sync_runtime",
    COMPONENT / "statistics_sync_runtime.py",
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class SyncRuntimeTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.runtime = module.MeterSyncRuntime()
        self.hass = SimpleNamespace(
            config=SimpleNamespace(time_zone="America/Los_Angeles")
        )
        self.meter = {"id": 1, "commodity": 1,
                      "display_name": "Electric"}
        self.api = SimpleNamespace(stream=AsyncMock(return_value={
            "physical_meter_id": 1,
            "resolved": True,
            "issues": [],
            "intervals": [],
        }))

    async def test_close_rejects_new_work_and_reopen_allows_it(self):
        self.runtime.begin_close()
        with self.assertRaises(module.StatisticsSyncError):
            await self.runtime.sync_meter(
                self.hass, self.api, self.meter, confirmed=True
            )
        self.api.stream.assert_not_awaited()
        self.runtime.reopen()
        self.assertFalse(self.runtime._closing)

    async def test_requires_explicit_confirmation(self):
        with self.assertRaises(module.StatisticsSyncError):
            await self.runtime.sync_meter(self.hass, self.api, self.meter)
        self.api.stream.assert_not_called()

    async def test_rejects_wrong_meter_without_recorder_write(self):
        self.api.stream.return_value["physical_meter_id"] = 2
        with patch.object(module, "sync_owned_statistics") as writer:
            with self.assertRaises(module.StatisticsSyncError):
                await self.runtime.sync_meter(
                    self.hass, self.api, self.meter, confirmed=True
                )
            writer.assert_not_called()

    async def test_rejects_unresolved_without_recorder_write(self):
        self.api.stream.return_value["resolved"] = False
        with patch.object(module, "sync_owned_statistics") as writer:
            with self.assertRaises(Exception):
                await self.runtime.sync_meter(
                    self.hass, self.api, self.meter, confirmed=True
                )
            writer.assert_not_called()

    async def test_calls_recorder_only_after_canonical_validation(self):
        stream = self.api.stream.return_value
        stream["intervals"] = [{
            "start_utc": "2026-10-01T00:00:00Z",
            "duration_seconds": 3600,
            "raw_value": 1000,
            "power_of_ten_multiplier": 0,
            "unit_of_measure": 72,
            "accepted_revision_id": 33,
        }]
        plan = SimpleNamespace(added=1, corrected=0, unchanged=0,
                               rows=({"start": None},))
        with patch.object(
            module, "sync_owned_statistics", new_callable=AsyncMock,
            return_value=plan,
        ) as writer, patch.object(
            module, "wait_for_persisted_statistics",
            new_callable=AsyncMock,
            return_value=SimpleNamespace(observations=1),
        ):
            result = await self.runtime.sync_meter(
                self.hass, self.api, self.meter, confirmed=True
            )
            self.assertEqual(result.added, 1)
            self.assertTrue(result.queued)
            batch = writer.await_args.args[1]
            self.assertEqual(batch.statistic_id,
                             "energy_usage:electricity_meter_1")
            self.assertEqual(batch.rows[0]["state"], 1.0)

    async def test_serializes_two_requests_for_same_meter(self):
        stream = self.api.stream.return_value
        stream["intervals"] = [{
            "start_utc": "2026-10-01T00:00:00Z",
            "duration_seconds": 3600,
            "raw_value": 500,
            "power_of_ten_multiplier": 0,
            "unit_of_measure": 72,
            "accepted_revision_id": 21,
        }]
        active = 0
        max_active = 0

        async def fake_writer(*args, **kwargs):
            nonlocal active, max_active
            active += 1
            max_active = max(max_active, active)
            await asyncio.sleep(0)
            active -= 1
            return SimpleNamespace(added=0, corrected=0, unchanged=1,
                                   rows=({"start": None},))

        with patch.object(module, "sync_owned_statistics",
                          side_effect=fake_writer), patch.object(
            module, "wait_for_persisted_statistics",
            new_callable=AsyncMock,
            return_value=SimpleNamespace(observations=1),
        ):
            await asyncio.gather(*(
                self.runtime.sync_meter(
                    self.hass, self.api, self.meter, confirmed=True
                ) for _ in range(2)
            ))
        self.assertEqual(max_active, 1)

    async def test_drain_waits_for_admitted_work(self):
        entered = asyncio.Event()
        release = asyncio.Event()

        async def blocked_stream(_meter_id):
            entered.set()
            await release.wait()
            raise RuntimeError("API temporarily unavailable")

        self.api.stream.side_effect = blocked_stream
        task = asyncio.create_task(self.runtime.sync_meter(
            self.hass, self.api, self.meter, confirmed=True
        ))
        await entered.wait()
        drain = asyncio.create_task(self.runtime.drain())
        await asyncio.sleep(0)
        self.assertFalse(drain.done())
        with self.assertRaisesRegex(module.StatisticsSyncError, "closing"):
            await self.runtime.sync_meter(
                self.hass, self.api, self.meter, confirmed=True
            )
        release.set()
        with self.assertRaisesRegex(RuntimeError, "unavailable"):
            await task
        await drain
        self.assertFalse(self.runtime._active)

    async def test_failed_request_releases_runtime_slot(self):
        self.api.stream.side_effect = RuntimeError("temporary outage")
        with self.assertRaises(RuntimeError):
            await self.runtime.sync_meter(
                self.hass, self.api, self.meter, confirmed=True
            )
        self.assertFalse(self.runtime._active)
        self.api.stream.side_effect = None
        with self.assertRaisesRegex(
            module.StatisticsSyncError, "identity mismatch"
        ):
            await self.runtime.sync_meter(
                self.hass, self.api,
                {**self.meter, "id": 2}, confirmed=True
            )
        self.assertEqual(self.api.stream.await_count, 2)
