# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Read-only live Recorder preflight tests without HA runtime dependencies."""

import asyncio
import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PKG = "custom_components.energy_usage"
for name in ("custom_components", PKG):
    if name not in sys.modules:
        package = ModuleType(name)
        package.__path__ = [str(ROOT / name.replace(".", "/"))]
        sys.modules[name] = package

for part in ("history", "statistics_import", "statistics_sync_plan",
             "statistics_sync_recorder", "statistics_sync_preflight"):
    fqname = f"{PKG}.{part}"
    if fqname not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            fqname, ROOT / "custom_components/energy_usage" / f"{part}.py"
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[fqname] = module
        spec.loader.exec_module(module)

from custom_components.energy_usage.statistics_sync_preflight import (
    assess_meter,
)
from custom_components.energy_usage.statistics_sync_plan import (
    StatisticsSyncError,
)

START = datetime(2026, 10, 6, tzinfo=timezone.utc)


def interval(hour, value, revision):
    return {
        "start_utc": f"2026-10-06T{hour:02d}:00:00Z",
        "duration_seconds": 3600,
        "raw_value": value,
        "unit_of_measure": 72,
        "power_of_ten_multiplier": 0,
        "accepted_revision_id": revision,
        "meter_reading_id": 11,
    }


class FakeApi:
    def __init__(self, rows, *, resolved=True):
        self.rows = rows
        self.resolved = resolved

    async def stream(self, meter_id):
        return {
            "physical_meter_id": meter_id,
            "resolved": self.resolved,
            "issues": [],
            "intervals": self.rows,
        }


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.hass = SimpleNamespace(
            config=SimpleNamespace(time_zone="America/Los_Angeles")
        )
        self.meter = {
            "id": 1, "commodity": 1, "display_name": "Electric"
        }
        self.api = FakeApi([interval(0, 1000, 1), interval(1, 2000, 2)])

    def test_empty_history_plans_initial_sync(self):
        async def read(*args):
            return []
        result = asyncio.run(assess_meter(
            self.hass, self.api, self.meter, read_statistics=read
        ))
        self.assertEqual((result.existing, result.added,
                          result.corrected), (0, 2, 0))

    def test_populated_history_plans_append(self):
        async def read(*args):
            return [{"start": START, "state": 1, "sum": 1}]
        result = asyncio.run(assess_meter(
            self.hass, self.api, self.meter, read_statistics=read
        ))
        self.assertEqual((result.added, result.corrected,
                          result.unchanged), (1, 0, 1))

    def test_replay_plans_no_writes(self):
        async def read(*args):
            return [
                {"start": START, "state": 1, "sum": 1},
                {"start": START.replace(hour=1), "state": 2, "sum": 3},
            ]
        result = asyncio.run(assess_meter(
            self.hass, self.api, self.meter, read_statistics=read
        ))
        self.assertEqual((result.added, result.corrected), (0, 0))

    def test_missing_canonical_resolution_rejected(self):
        async def read(*args):
            self.fail("Recorder must not be read for unresolved source")
        with self.assertRaises(StatisticsSyncError):
            asyncio.run(assess_meter(
                self.hass, FakeApi(self.api.rows, resolved=False),
                self.meter, read_statistics=read,
            ))

    def test_mismatched_baseline_rejected(self):
        async def read(*args):
            return [{"start": START, "state": 9, "sum": 9}]
        with self.assertRaises(StatisticsSyncError):
            asyncio.run(assess_meter(
                self.hass, self.api, self.meter, read_statistics=read
            ))


if __name__ == "__main__":
    unittest.main()
