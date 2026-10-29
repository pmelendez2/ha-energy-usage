# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Safety tests for empty- and populated-series synchronization plans."""

import importlib.util
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

path = (Path(__file__).resolve().parents[1]
        / "custom_components/energy_usage/statistics_sync_plan.py")
spec = importlib.util.spec_from_file_location("statistics_sync_plan", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def at(day):
    return datetime(2026, 10, day, tzinfo=timezone.utc)


def row(day, value, total):
    return {"start": at(day), "state": value, "sum": total}


class StatisticsSyncPlanTests(unittest.TestCase):
    def test_empty_installation_can_plan_initial_history(self):
        plan = module.plan_statistics_sync(
            [], [row(1, 1, 1), row(2, 2, 3)]
        )
        self.assertEqual(plan.mode, "initial")
        self.assertEqual((plan.added, plan.corrected), (2, 0))
        self.assertEqual(plan.rows[-1]["sum"], 3)

    def test_populated_series_appends_and_corrects(self):
        plan = module.plan_statistics_sync(
            [row(1, 1, 1), row(2, 2, 3)],
            [row(1, 1.5, 1.5), row(2, 2, 3.5),
             row(3, 4, 7.5)],
        )
        self.assertEqual(plan.mode, "reconcile")
        self.assertEqual((plan.added, plan.corrected,
                          plan.unchanged), (1, 1, 1))
        self.assertEqual(plan.rows[-1]["sum"], 7.5)
        self.assertEqual(plan.first_changed, at(1))

    def test_idempotent_replay(self):
        rows = [row(1, 1, 1), row(2, 2, 3)]
        plan = module.plan_statistics_sync(rows, rows)
        self.assertEqual((plan.added, plan.corrected), (0, 0))
        self.assertIsNone(plan.first_changed)

    def test_never_deletes_existing_recordings(self):
        with self.assertRaises(module.StatisticsSyncError):
            module.plan_statistics_sync(
                [row(1, 1, 1), row(2, 2, 3)],
                [row(2, 2, 2)],
            )

    def test_unrelated_history_is_rejected(self):
        with self.assertRaises(module.StatisticsSyncError):
            module.plan_statistics_sync(
                [row(1, 1, 1)], [row(2, 2, 2)]
            )

    def test_duplicate_or_unordered_readings_rejected(self):
        for bad in ([row(1, 1, 1), row(1, 2, 3)],
                    [row(2, 2, 2), row(1, 1, 3)]):
            with self.subTest(bad=bad):
                with self.assertRaises(module.StatisticsSyncError):
                    module.plan_statistics_sync([], bad)

    def test_nan_rejected(self):
        with self.assertRaises(module.StatisticsSyncError):
            module.plan_statistics_sync([], [row(1, float("nan"), 1)])


if __name__ == "__main__":
    unittest.main()
