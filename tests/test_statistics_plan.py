# SPDX-License-Identifier: MIT
"""Regression tests for read-only electricity statistic planning."""

import importlib.util
import sys
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

SOURCE = (
    Path(__file__).resolve().parents[1]
    / "custom_components/energy_usage/statistics_plan.py"
)
spec = importlib.util.spec_from_file_location("energy_statistics_plan", SOURCE)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def observation(hour, value="1", *, unit="kWh", duration=1, revision=1):
    start = T0 + timedelta(hours=hour)
    return SimpleNamespace(
        start_utc=start,
        end_utc=start + timedelta(hours=duration),
        value=Decimal(value), unit=unit, revision_id=revision,
    )


class StatisticsPlanTests(unittest.TestCase):
    """Ensure the plan is deterministic, conservative, and gap-safe."""

    def test_empty_is_empty(self):
        self.assertEqual(module.plan_hourly_electricity([]), ())

    def test_cumulative_usage(self):
        result = module.plan_hourly_electricity([
            observation(1, "2"), observation(0, "1.5")
        ])
        self.assertEqual([x.sum for x in result], [
            Decimal("1.5"), Decimal("3.5")
        ])

    def test_gap_has_no_synthetic_row(self):
        result = module.plan_hourly_electricity([
            observation(0), observation(2)
        ])
        self.assertEqual([x.start for x in result], [
            T0, T0 + timedelta(hours=2)
        ])

    def test_correction_changes_subsequent_totals(self):
        old = module.plan_hourly_electricity([
            observation(0, "1"), observation(1, "2")
        ])
        updated = module.plan_hourly_electricity([
            observation(0, "3", revision=2), observation(1, "2")
        ])
        self.assertEqual(old[-1].sum, Decimal("3"))
        self.assertEqual(updated[-1].sum, Decimal("5"))

    def test_repeated_calculation_is_identical(self):
        rows = [observation(0), observation(1)]
        self.assertEqual(
            module.plan_hourly_electricity(rows),
            module.plan_hourly_electricity(rows),
        )

    def test_duplicates_rejected(self):
        with self.assertRaises(module.StatisticsPlanError):
            module.plan_hourly_electricity([
                observation(0), observation(0)
            ])

    def test_overlap_rejected(self):
        with self.assertRaises(module.StatisticsPlanError):
            module.plan_hourly_electricity([
                observation(0, duration=2), observation(1)
            ])

    def test_gas_is_not_misclassified(self):
        with self.assertRaises(module.StatisticsPlanError):
            module.plan_hourly_electricity([
                observation(0, unit="therm")
            ])

    def test_negative_and_nan_rejected(self):
        for value in ("-1", "NaN", "Infinity"):
            with self.subTest(value=value):
                with self.assertRaises(module.StatisticsPlanError):
                    module.plan_hourly_electricity([
                        observation(0, value)
                    ])

    def test_unaligned_interval_rejected(self):
        row = observation(0)
        row.start_utc += timedelta(minutes=10)
        # An offset interval is valid source data, but it is not a
        # complete hourly statistic and must remain unreported.
        self.assertEqual(module.plan_hourly_electricity([row]), ())

    def test_wrong_duration_rejected(self):
        with self.assertRaises(module.StatisticsPlanError):
            module.plan_hourly_electricity([observation(0, duration=24)])

    def test_invalid_revision_rejected(self):
        with self.assertRaises(module.StatisticsPlanError):
            module.plan_hourly_electricity([
                observation(0, revision=0)
            ])


if __name__ == "__main__":
    unittest.main()
