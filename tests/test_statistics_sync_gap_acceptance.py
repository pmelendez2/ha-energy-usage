# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Isolated acceptance tests for actual late data and unfilled gaps."""

import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest

PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components/energy_usage/statistics_sync_plan.py"
)
SPEC = importlib.util.spec_from_file_location(
    "statistics_sync_plan_gap_acceptance", PATH
)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def row(offset, value, total, *, daily=False):
    unit = timedelta(days=1) if daily else timedelta(hours=1)
    return {
        "start": BASE + offset * unit,
        "state": value,
        "sum": total,
    }


class GapAcceptanceTests(unittest.TestCase):
    def test_electricity_gap_remains_absent(self):
        canonical = [row(0, 1, 1), row(2, 3, 4)]
        plan = MODULE.plan_statistics_sync([], canonical)
        self.assertEqual(plan.added, 2)
        self.assertEqual(
            [item["start"] for item in plan.rows],
            [item["start"] for item in canonical],
        )
        self.assertEqual([item["sum"] for item in plan.rows], [1, 4])

    def test_gas_daily_gap_remains_absent(self):
        canonical = [
            row(0, 1.25, 1.25, daily=True),
            row(3, 0.5, 1.75, daily=True),
        ]
        plan = MODULE.plan_statistics_sync([], canonical)
        self.assertEqual(len(plan.rows), 2)
        self.assertEqual(
            [item["start"] for item in plan.rows],
            [item["start"] for item in canonical],
        )

    def test_late_hourly_observation_only_adds_actual_point(self):
        existing = [row(0, 1, 1), row(2, 3, 4)]
        canonical = [row(0, 1, 1), row(1, 2, 3), row(2, 3, 6)]
        plan = MODULE.plan_statistics_sync(existing, canonical)
        self.assertEqual(
            (plan.added, plan.corrected, plan.unchanged),
            (1, 0, 2),
        )
        self.assertEqual(plan.first_changed, canonical[1]["start"])
        self.assertEqual([r["sum"] for r in plan.rows], [1, 3, 6])
        replay = MODULE.plan_statistics_sync(plan.rows, canonical)
        self.assertEqual((replay.added, replay.corrected), (0, 0))
        self.assertIsNone(replay.first_changed)

    def test_late_daily_observation_preserves_other_gaps(self):
        existing = [
            row(0, 1, 1, daily=True),
            row(4, 2, 3, daily=True),
        ]
        canonical = [
            row(0, 1, 1, daily=True),
            row(2, 0.5, 1.5, daily=True),
            row(4, 2, 3.5, daily=True),
        ]
        plan = MODULE.plan_statistics_sync(existing, canonical)
        self.assertEqual((plan.added, plan.corrected), (1, 0))
        self.assertEqual(len(plan.rows), 3)
        self.assertEqual([r["sum"] for r in plan.rows], [1, 1.5, 3.5])

    def test_correction_updates_downstream_sums_not_states(self):
        existing = [row(0, 1, 1), row(2, 2, 3), row(5, 4, 7)]
        canonical = [row(0, 1, 1), row(2, 3, 4), row(5, 4, 8)]
        plan = MODULE.plan_statistics_sync(existing, canonical)
        self.assertEqual(
            (plan.added, plan.corrected, plan.unchanged),
            (0, 1, 2),
        )
        self.assertEqual([r["state"] for r in plan.rows], [1, 3, 4])
        self.assertEqual([r["sum"] for r in plan.rows], [1, 4, 8])
        self.assertEqual(plan.first_changed, canonical[1]["start"])
        replay = MODULE.plan_statistics_sync(plan.rows, canonical)
        self.assertEqual((replay.added, replay.corrected), (0, 0))

    def test_missing_existing_observation_is_not_deleted(self):
        existing = [row(0, 1, 1), row(2, 3, 4)]
        with self.assertRaises(MODULE.StatisticsSyncError):
            MODULE.plan_statistics_sync(existing, [row(2, 3, 3)])


if __name__ == "__main__":
    unittest.main()
