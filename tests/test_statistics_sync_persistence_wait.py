# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Persistence-contract tests without a running Home Assistant instance."""

import asyncio
import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
PKG = "custom_components.energy_usage"
for name in ("custom_components", PKG):
    if name not in sys.modules:
        package = ModuleType(name)
        package.__path__ = [str(ROOT / name.replace(".", "/"))]
        sys.modules[name] = package
for part in ("statistics_sync_plan", "statistics_sync_verify",
             "statistics_sync_completion"):
    fullname = f"{PKG}.{part}"
    if fullname not in sys.modules:
        path = ROOT / "custom_components/energy_usage" / f"{part}.py"
        spec = importlib.util.spec_from_file_location(fullname, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[fullname] = module
        spec.loader.exec_module(module)

from custom_components.energy_usage.statistics_sync_completion import (
    wait_for_persisted_statistics,
)
from custom_components.energy_usage.statistics_sync_plan import (
    StatisticsSyncError,
)

STAMP = datetime(2026, 10, 6, tzinfo=timezone.utc)
EXPECTED = ({"start": STAMP, "state": 1.0, "sum": 1.0},)
ID = "energy_usage:electricity_meter_1"


class PersistenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_empty_then_persisted(self):
        calls = 0
        async def reader(*args):
            nonlocal calls
            calls += 1
            return [] if calls == 1 else EXPECTED
        async def no_sleep(_):
            pass
        result = await wait_for_persisted_statistics(
            None, ID, EXPECTED, read_statistics=reader,
            sleep=no_sleep, attempts=3,
        )
        self.assertEqual(result.observations, 1)
        self.assertEqual(calls, 2)

    async def test_correction_waits_for_updated_recorder_sum(self):
        calls = 0
        async def reader(*args):
            nonlocal calls
            calls += 1
            return [{**EXPECTED[0], "sum": 0.5}] if calls == 1 else EXPECTED
        async def no_sleep(_):
            pass
        result = await wait_for_persisted_statistics(
            None, ID, EXPECTED, read_statistics=reader,
            sleep=no_sleep, attempts=2,
        )
        self.assertEqual(result.observations, 1)

    async def test_never_claims_success_on_timeout(self):
        async def reader(*args):
            return []
        async def no_sleep(_):
            pass
        with self.assertRaisesRegex(StatisticsSyncError, "did not persist"):
            await wait_for_persisted_statistics(
                None, ID, EXPECTED, read_statistics=reader,
                sleep=no_sleep, attempts=2,
            )

    async def test_reader_failure_propagates(self):
        async def reader(*args):
            raise RuntimeError("Recorder unavailable")
        with self.assertRaisesRegex(RuntimeError, "unavailable"):
            await wait_for_persisted_statistics(
                None, ID, EXPECTED, read_statistics=reader,
            )

    async def test_rejects_foreign_statistic(self):
        with self.assertRaises(StatisticsSyncError):
            await wait_for_persisted_statistics(None, "sensor:bad", EXPECTED)
