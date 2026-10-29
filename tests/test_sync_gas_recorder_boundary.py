# SPDX-License-Identifier: MIT
"""Regression: gas local-day statistics are not UTC-hour aligned."""

import asyncio
import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PKG = 'custom_components.energy_usage'
for name in ('custom_components', PKG):
    if name not in sys.modules:
        package = ModuleType(name)
        package.__path__ = [str(ROOT / name.replace('.', '/'))]
        sys.modules[name] = package
for part in ('statistics_sync_plan', 'statistics_sync_recorder'):
    fqname = f'{PKG}.{part}'
    if fqname not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            fqname, ROOT / 'custom_components/energy_usage' / f'{part}.py'
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules[fqname] = mod
        spec.loader.exec_module(mod)

from custom_components.energy_usage.statistics_sync_recorder import (
    normalize_recorder_rows, read_owned_statistics,
)
from custom_components.energy_usage.statistics_sync_plan import StatisticsSyncError


class GasBoundaryTest(unittest.TestCase):
    def test_gas_utc_start_not_on_exact_hour(self):
        stamp = datetime(2025, 11, 2, 7, 0, tzinfo=timezone.utc)
        shifted = datetime(2025, 11, 3, 8, 0, tzinfo=timezone.utc)
        rows = normalize_recorder_rows([
            {'start': stamp.timestamp() + 60, 'state': 1, 'sum': 1},
            {'start': shifted.timestamp() + 60, 'state': 2, 'sum': 3},
        ])
        self.assertEqual(rows[0]['start'].minute, 1)
        self.assertEqual(rows[1]['start'].minute, 1)

    def test_reject_misaligned_electricity_from_reader(self):
        recorder = ModuleType('homeassistant.components.recorder')
        stats = ModuleType('homeassistant.components.recorder.statistics')
        recorder.get_instance = lambda hass: SimpleNamespace(
            async_add_executor_job=lambda fn, *args: asyncio.sleep(
                0, result={'energy_usage:electricity_meter_1': [
                    {'start': 1791244860, 'state': 1, 'sum': 1}
                ]}
            )
        )
        stats.statistics_during_period = lambda *a: None
        with patch.dict(sys.modules, {
            'homeassistant': ModuleType('homeassistant'),
            'homeassistant.components': ModuleType('homeassistant.components'),
            'homeassistant.components.recorder': recorder,
            'homeassistant.components.recorder.statistics': stats,
        }):
            with self.assertRaises(StatisticsSyncError):
                asyncio.run(read_owned_statistics(
                    None, 'energy_usage:electricity_meter_1',
                    datetime(2025, 1, 1, tzinfo=timezone.utc),
                    datetime(2027, 1, 1, tzinfo=timezone.utc),
                ))


if __name__ == '__main__':
    unittest.main()
