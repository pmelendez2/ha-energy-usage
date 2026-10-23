# SPDX-License-Identifier: MIT
"""Independent regression tests for graph-ready utility statistics."""

import importlib.util
import pathlib
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[1]
PKG = "custom_components.energy_usage"
# Load pure helper without importing the Home Assistant runtime.
for name, path in [
    (PKG, ROOT / "custom_components/energy_usage"),
]:
    module = types.ModuleType(name)
    module.__path__ = [str(path)]
    sys.modules.setdefault(name, module)
for part in ("history", "statistics_import"):
    name = f"{PKG}.{part}"
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "custom_components/energy_usage" / f"{part}.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

from custom_components.energy_usage.history import UsageInterval
from custom_components.energy_usage.statistics_import import (
    StatisticsImportError, build_statistics,
)

UTC = timezone.utc
T = datetime(2026, 10, 1, tzinfo=UTC)


def reading(hours=0, value="1.25", duration=1, unit="kWh"):
    start = T + timedelta(hours=hours)
    return UsageInterval(
        start, start + timedelta(hours=duration), Decimal(value),
        unit, 1,
    )


class StatisticsTests(unittest.TestCase):
    def test_hourly_total(self):
        batch = build_statistics(1, 1, "Electric", [
            reading(), reading(1, "2.0")
        ])
        self.assertEqual(batch.statistic_id,
                         "energy_usage:electricity_meter_1")
        self.assertEqual([x["sum"] for x in batch.rows], [1.25, 3.25])

    def test_missing_hour_not_inserted(self):
        batch = build_statistics(1, 1, "Electric", [
            reading(), reading(3)
        ])
        self.assertEqual(len(batch.rows), 2)
        self.assertEqual(batch.missing_intervals, 2)

    def test_duplicate_rejected(self):
        with self.assertRaises(StatisticsImportError):
            build_statistics(1, 1, "Electric", [reading(), reading()])

    def test_negative_rejected(self):
        with self.assertRaises(StatisticsImportError):
            build_statistics(1, 1, "Electric", [reading(value="-1")])

    def test_non_hourly_electricity_rejected(self):
        with self.assertRaises(StatisticsImportError):
            build_statistics(1, 1, "Electric", [reading(duration=2)])

    def test_gas_daily_not_hourly(self):
        from zoneinfo import ZoneInfo
        local = ZoneInfo("America/Los_Angeles")
        dates = [datetime(2026, 10, d, 23, 59, tzinfo=local)
                 for d in (1, 3)]
        observations = [UsageInterval(
            d.astimezone(UTC),
            d.astimezone(UTC) + timedelta(days=1),
            Decimal("1.25"), "therm", 1,
        ) for d in dates]
        batch = build_statistics(
            2, 7, "Gas", observations,
            time_zone="America/Los_Angeles",
        )
        self.assertEqual(batch.unit, "therm")
        self.assertEqual(batch.missing_intervals, 1)
        self.assertEqual(len(batch.rows), 2)

    def test_sdge_gas_2359_pacific(self):
        from zoneinfo import ZoneInfo
        local = ZoneInfo("America/Los_Angeles")
        dates = [datetime(2025, 11, d, 23, 59, tzinfo=local)
                 for d in (1, 2, 3)]
        intervals = [UsageInterval(
            d.astimezone(UTC),
            d.astimezone(UTC) + timedelta(days=1),
            Decimal("1.5"), "therm", 1,
        ) for d in dates]
        batch = build_statistics(
            2, 7, "Gas", intervals,
            time_zone="America/Los_Angeles",
        )
        self.assertEqual(len(batch.rows), 3)
        self.assertEqual(batch.missing_intervals, 0)
        self.assertEqual(batch.rows[-1]["sum"], 4.5)
        self.assertTrue(all(
            row["start"].astimezone(local).hour == 0
            for row in batch.rows
        ))

    def test_sdge_gas_missing_day(self):
        from zoneinfo import ZoneInfo
        local = ZoneInfo("America/Los_Angeles")
        dates = [datetime(2026, 10, d, 23, 59, tzinfo=local)
                 for d in (1, 3)]
        intervals = [UsageInterval(
            d.astimezone(UTC),
            d.astimezone(UTC) + timedelta(days=1),
            Decimal("2"), "therm", 1,
        ) for d in dates]
        batch = build_statistics(
            2, 7, "Gas", intervals,
            time_zone="America/Los_Angeles",
        )
        self.assertEqual(batch.missing_intervals, 1)
        self.assertEqual(len(batch.rows), 2)

    def test_empty_rejected(self):
        with self.assertRaises(StatisticsImportError):
            build_statistics(2, 7, "Gas", [])

    def test_unsupported_meter_rejected(self):
        with self.assertRaises(StatisticsImportError):
            build_statistics(2, 2, "Other", [reading()])


if __name__ == "__main__":
    unittest.main()
