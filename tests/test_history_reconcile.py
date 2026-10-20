# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Project Contributors
"""Validate historical usage reconciliation without Home Assistant."""

import importlib.util
import sys
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace


PATH = (Path(__file__).resolve().parents[1]
        / "custom_components/energy_usage/history_reconcile.py")
SPEC = importlib.util.spec_from_file_location(
    "energy_usage_reconcile_unit", PATH
)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
plan_usage_changes = MODULE.plan_usage_changes


def row(day=1, value="1.0", revision=1, unit="kWh", hours=1):
    """Produce one synthetic, normalized interval."""
    start = datetime(2026, 1, day, tzinfo=timezone.utc)
    return SimpleNamespace(
        start_utc=start,
        end_utc=start + timedelta(hours=hours),
        value=Decimal(value), unit=unit, revision_id=revision,
    )


class ReconciliationTests(unittest.TestCase):
    """Check expected gaps, duplicates, and correction behavior."""

    def test_new_older_gap_is_added(self):
        result = plan_usage_changes([row(2)], [row(1), row(2)])
        self.assertEqual(len(result.added), 1)
        self.assertEqual(result.added[0].start_utc.day, 1)

    def test_partial_month_does_not_delete_stored_history(self):
        result = plan_usage_changes([row(1), row(2)], [row(2)])
        self.assertEqual(result.added, ())
        self.assertEqual(result.corrected, ())
        self.assertEqual(len(result.unchanged), 1)

    def test_accepted_revision_with_new_value_is_correction(self):
        result = plan_usage_changes([row(value="1")],
                                    [row(value="1.5", revision=2)])
        self.assertEqual(len(result.corrected), 1)
        self.assertEqual(result.corrected[0].value, Decimal("1.5"))

    def test_revision_only_change_does_not_change_usage(self):
        result = plan_usage_changes([row()], [row(revision=3)])
        self.assertEqual(len(result.unchanged), 1)
        self.assertEqual(result.corrected, ())

    def test_duplicate_or_overlapping_input_is_rejected(self):
        with self.assertRaises(ValueError):
            plan_usage_changes([], [row(), row()])
        with self.assertRaises(ValueError):
            plan_usage_changes([], [row(hours=30), row(2)])

    def test_units_do_not_mix(self):
        with self.assertRaises(ValueError):
            plan_usage_changes([row()], [row(unit="therm")])

    def test_changed_duration_requires_explicit_resolution(self):
        with self.assertRaises(ValueError):
            plan_usage_changes([row()], [row(hours=2)])

    def test_non_finite_and_negative_values_rejected(self):
        for bad in ("NaN", "Infinity", "-1"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                plan_usage_changes([], [row(value=bad)])


if __name__ == "__main__":
    unittest.main()
