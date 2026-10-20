# SPDX-License-Identifier: MIT
"""Standalone ADR-0001 regression tests without HA runtime imports."""

import importlib.util
import sys
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import ModuleType, SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
PKG = "custom_components.energy_usage"
for name in ("custom_components", PKG):
    if name not in sys.modules:
        package = ModuleType(name)
        package.__path__ = [str(ROOT / name.replace(".", "/"))]
        sys.modules[name] = package


def load(name):
    path = ROOT / "custom_components/energy_usage" / f"{name}.py"
    fqname = f"{PKG}.{name}"
    spec = importlib.util.spec_from_file_location(fqname, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[fqname] = module
    spec.loader.exec_module(module)
    return module


planner = load("statistics_plan")
preview = load("statistics_preview")
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def row(minute, length=15, amount="0.5", revision=1):
    start = T0 + timedelta(minutes=minute)
    return SimpleNamespace(
        start_utc=start, end_utc=start + timedelta(minutes=length),
        value=Decimal(amount), unit="kWh", revision_id=revision,
    )


class Adr0001Tests(unittest.TestCase):
    """Validate coverage, corrections, and dry-run output."""

    def test_four_quarters_complete(self):
        plan = planner.plan_electricity_hours([
            row(45), row(0), row(30), row(15)
        ])
        self.assertEqual(len(plan.points), 1)
        self.assertEqual(plan.points[0].sum, Decimal("2.0"))
        self.assertFalse(plan.incomplete_hours)

    def test_incomplete_quarter_is_missing(self):
        plan = planner.plan_electricity_hours([
            row(0), row(15), row(45)
        ])
        self.assertFalse(plan.points)
        self.assertEqual(plan.incomplete_hours, (T0,))

    def test_incomplete_hour_not_in_cumulative(self):
        plan = planner.plan_electricity_hours([
            row(0, 60, "3"), row(60), row(75),
            row(120, 60, "2")
        ])
        self.assertEqual([p.sum for p in plan.points], [
            Decimal("3"), Decimal("5")
        ])
        self.assertEqual(plan.incomplete_hours, (T0 + timedelta(hours=1),))

    def test_late_quarter_changes_later_totals(self):
        before = planner.plan_electricity_hours([
            row(0), row(15), row(45), row(60, 60, "2")
        ])
        after = planner.plan_electricity_hours([
            row(0), row(15), row(30), row(45),
            row(60, 60, "2")
        ])
        self.assertEqual(before.points[-1].sum, Decimal("2"))
        self.assertEqual(after.points[-1].sum, Decimal("4"))

    def test_revision_correction_propagates(self):
        original = planner.plan_electricity_hours([
            row(0, 60, "1"), row(60, 60, "2")
        ])
        corrected = planner.plan_electricity_hours([
            row(0, 60, "3", revision=2), row(60, 60, "2")
        ])
        self.assertEqual(original.points[-1].sum, Decimal("3"))
        self.assertEqual(corrected.points[-1].sum, Decimal("5"))

    def test_duplicate_rejected(self):
        with self.assertRaises(planner.StatisticsPlanError):
            planner.plan_electricity_hours([row(0), row(0)])

    def test_cross_hour_rejected(self):
        with self.assertRaises(planner.StatisticsPlanError):
            planner.plan_electricity_hours([row(45, 30)])

    def test_invalid_values_rejected(self):
        for value in ("-1", "NaN", "Infinity"):
            with self.subTest(value=value):
                with self.assertRaises(planner.StatisticsPlanError):
                    planner.plan_electricity_hours([row(0, 60, value)])

    def test_stable_external_id(self):
        self.assertEqual(preview.electricity_statistic_id(7),
                         "energy_usage:electricity_meter_7")
        for invalid in (0, -1, True, "7"):
            with self.assertRaises(ValueError):
                preview.electricity_statistic_id(invalid)

    def test_preview_is_read_only_and_preserves_gaps(self):
        plan = planner.plan_electricity_hours([
            row(0, 60), row(120, 60)
        ])
        result = preview.preview_electricity(1, plan)
        self.assertEqual(result.metadata["unit_class"], "energy")
        self.assertEqual(result.metadata["source"], "energy_usage")
        self.assertEqual(len(result.statistics), 2)
        self.assertEqual(result.statistics[-1]["sum"], 1.0)
        self.assertFalse(result.incomplete_hours)

    def test_repeat_preview_is_deterministic(self):
        plan = planner.plan_electricity_hours([row(0, 60)])
        self.assertEqual(preview.preview_electricity(1, plan),
                         preview.preview_electricity(1, plan))


if __name__ == "__main__":
    unittest.main()
