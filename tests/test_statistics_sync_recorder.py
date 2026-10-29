# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Guarded synchronization adapter regression tests (no HA dependency)."""

import asyncio
import importlib.util
import sys
import unittest
from datetime import datetime, timezone
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

for part in ("statistics_sync_plan", "statistics_sync_recorder"):
    fqname = f"{PKG}.{part}"
    path = ROOT / "custom_components/energy_usage" / f"{part}.py"
    spec = importlib.util.spec_from_file_location(fqname, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[fqname] = module
    spec.loader.exec_module(module)

from custom_components.energy_usage.statistics_sync_plan import (
    StatisticsSyncError,
)
from custom_components.energy_usage.statistics_sync_recorder import (
    normalize_recorder_rows,
    sync_owned_statistics,
    validate_owned_baseline,
)


START = datetime(2026, 10, 6, tzinfo=timezone.utc)


def row(state, total, *, stamp=START):
    return {"start": stamp, "state": state, "sum": total}


class RecorderAdapterTests(unittest.TestCase):
    def test_recorder_unix_timestamps(self):
        actual = normalize_recorder_rows([{
            "start": START.timestamp(), "state": 1, "sum": 1,
        }])
        self.assertEqual(actual, [row(1, 1)])

    def test_gas_dst_shifted_utc_timestamp(self):
        actual = normalize_recorder_rows([{
            "start": START.timestamp() + 60,
            "state": 1, "sum": 1,
        }])
        self.assertEqual(actual[0]["start"].minute, 1)

    def test_reject_missing_sum(self):
        with self.assertRaises(StatisticsSyncError):
            normalize_recorder_rows([{"start": START, "state": 1}])

    def test_reject_invalid_baseline(self):
        with self.assertRaises(StatisticsSyncError):
            validate_owned_baseline([row(1, 55)], [row(1, 1)])

    def test_accept_empty_baseline(self):
        validate_owned_baseline([], [row(1, 1)])

    def test_accept_matching_baseline(self):
        validate_owned_baseline([row(1, 1)], [row(1, 1)])

    def test_sync_requires_explicit_confirmation(self):
        batch = SimpleNamespace(statistic_id="energy_usage:gas_meter_2",
                                rows=(row(1, 1),), unit="thm")
        with self.assertRaises(StatisticsSyncError):
            asyncio.run(sync_owned_statistics(None, batch))

    def test_sync_unchanged_never_writes(self):
        batch = SimpleNamespace(
            statistic_id="energy_usage:electricity_meter_1",
            rows=(row(1, 1),), unit="kWh", name="Electric",
        )
        async def mock_read(*_args):
            return [row(1, 1)]
        with patch(
            "custom_components.energy_usage.statistics_sync_recorder"
            ".read_owned_statistics", mock_read,
        ):
            plan = asyncio.run(sync_owned_statistics(
                None, batch, confirmed=True
            ))
        self.assertEqual((plan.added, plan.corrected), (0, 0))


if __name__ == "__main__":
    unittest.main()

class RecorderWriteTests(unittest.TestCase):
    def test_new_installation_queues_supported_api(self):
        batch = SimpleNamespace(
            statistic_id="energy_usage:electricity_meter_1",
            rows=(row(1, 1),), unit="kWh", name="Electric",
        )

        async def mock_read(*_args):
            return []

        recorder = ModuleType("homeassistant.components.recorder")
        models = ModuleType("homeassistant.components.recorder.models")
        statistics = ModuleType("homeassistant.components.recorder.statistics")
        models.StatisticMeanType = SimpleNamespace(NONE=0)
        models.StatisticMetaData = dict
        models.StatisticData = dict
        calls = []
        statistics.async_add_external_statistics = (
            lambda hass, meta, values: calls.append((meta, values))
        )
        with patch.dict(sys.modules, {
            "homeassistant": ModuleType("homeassistant"),
            "homeassistant.components": ModuleType("homeassistant.components"),
            "homeassistant.components.recorder": recorder,
            "homeassistant.components.recorder.models": models,
            "homeassistant.components.recorder.statistics": statistics,
        }), patch(
            "custom_components.energy_usage.statistics_sync_recorder"
            ".read_owned_statistics", mock_read,
        ):
            result = asyncio.run(sync_owned_statistics(
                None, batch, confirmed=True
            ))
        self.assertEqual(result.mode, "initial")
        self.assertEqual(result.added, 1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1][0]["sum"], 1.0)

    def test_populated_installation_queues_correction(self):
        from datetime import timedelta
        next_hour = START + timedelta(hours=1)
        batch = SimpleNamespace(
            statistic_id="energy_usage:electricity_meter_1",
            rows=(row(1, 1), row(3, 4, stamp=next_hour)),
            unit="kWh", name="Electric",
        )

        async def mock_read(*_args):
            return [row(1, 1), row(2, 3, stamp=next_hour)]

        recorder = ModuleType("homeassistant.components.recorder")
        models = ModuleType("homeassistant.components.recorder.models")
        statistics = ModuleType("homeassistant.components.recorder.statistics")
        models.StatisticMeanType = SimpleNamespace(NONE=0)
        models.StatisticMetaData = dict
        models.StatisticData = dict
        calls = []
        statistics.async_add_external_statistics = (
            lambda hass, meta, values: calls.append((meta, values))
        )
        with patch.dict(sys.modules, {
            "homeassistant": ModuleType("homeassistant"),
            "homeassistant.components": ModuleType("homeassistant.components"),
            "homeassistant.components.recorder": recorder,
            "homeassistant.components.recorder.models": models,
            "homeassistant.components.recorder.statistics": statistics,
        }), patch(
            "custom_components.energy_usage.statistics_sync_recorder"
            ".read_owned_statistics", mock_read,
        ):
            result = asyncio.run(sync_owned_statistics(
                None, batch, confirmed=True
            ))
        self.assertEqual(result.corrected, 1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1][-1]["sum"], 4.0)
