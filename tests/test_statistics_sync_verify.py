# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Read-back verification regression tests without HA runtime."""

import importlib.util
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
PKG = "custom_components.energy_usage"
for name in ("custom_components", PKG):
    if name not in sys.modules:
        package = ModuleType(name)
        package.__path__ = [str(ROOT / name.replace(".", "/"))]
        sys.modules[name] = package
for part in ("statistics_sync_plan", "statistics_sync_verify"):
    fqname = f"{PKG}.{part}"
    if fqname not in sys.modules:
        path = ROOT / "custom_components/energy_usage" / f"{part}.py"
        spec = importlib.util.spec_from_file_location(fqname, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[fqname] = module
        spec.loader.exec_module(module)

from custom_components.energy_usage.statistics_sync_plan import (
    StatisticsSyncError,
)
from custom_components.energy_usage.statistics_sync_verify import (
    verify_sync_persistence,
)

START = datetime(2026, 10, 6, tzinfo=timezone.utc)


def row(day, amount, total):
    return {"start": START + timedelta(days=day), "state": amount,
            "sum": total}


class PersistenceTests(unittest.TestCase):
    def check(self, expected, stored, complete=True):
        return verify_sync_persistence(
            "energy_usage:gas_meter_2", expected, stored,
            complete_readback=complete,
        )

    def test_empty_installation_after_import(self):
        expected = [row(0, 1, 1), row(1, 2, 3)]
        self.assertEqual(self.check(expected, expected).observations, 2)

    def test_populated_after_append_and_correction(self):
        expected = [row(0, 1, 1), row(1, 3, 4), row(2, 2, 6)]
        self.assertEqual(self.check(expected, expected).observations, 3)

    def test_pending_queue_not_persisted(self):
        expected = [row(0, 1, 1), row(1, 2, 3)]
        with self.assertRaises(
            verify_sync_persistence.__globals__["StatisticsSyncError"]
        ):
            self.check(expected, expected[:1])

    def test_wrong_cumulative_sum_fails(self):
        with self.assertRaises(
            verify_sync_persistence.__globals__["StatisticsSyncError"]
        ):
            self.check([row(0, 2, 2)], [row(0, 2, 1)])

    def test_wrong_state_fails(self):
        with self.assertRaises(
            verify_sync_persistence.__globals__["StatisticsSyncError"]
        ):
            self.check([row(0, 2, 2)], [row(0, 1, 2)])

    def test_extra_timestamp_fails(self):
        with self.assertRaises(
            verify_sync_persistence.__globals__["StatisticsSyncError"]
        ):
            self.check([row(0, 1, 1)], [row(0, 1, 1), row(1, 1, 2)])

    def test_incomplete_readback_rejected(self):
        with self.assertRaises(
            verify_sync_persistence.__globals__["StatisticsSyncError"]
        ):
            self.check([row(0, 1, 1)], [row(0, 1, 1)], False)

    def test_local_day_dst_utc_spacing_allowed(self):
        before = {"start": datetime(2025, 11, 2, 7, tzinfo=timezone.utc),
                  "state": 1.0, "sum": 1.0}
        after = {"start": datetime(2025, 11, 3, 8, tzinfo=timezone.utc),
                 "state": 2.0, "sum": 3.0}
        self.assertEqual(self.check([before, after], [before, after])
                         .observations, 2)

    def test_duplicate_timestamp_rejected(self):
        with self.assertRaises(
            verify_sync_persistence.__globals__["StatisticsSyncError"]
        ):
            self.check([row(0, 1, 1)], [row(0, 1, 1)] * 2)


if __name__ == "__main__":
    unittest.main()
