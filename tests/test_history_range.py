# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Check guided-import date selection with no Home Assistant runtime."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/energy_usage"
PKG = "_range_test"
pkg = types.ModuleType(PKG)
pkg.__path__ = [str(COMPONENT)]
sys.modules[PKG] = pkg
for part in ("history", "history_range"):
    spec = importlib.util.spec_from_file_location(
        f"{PKG}.{part}", COMPONENT / f"{part}.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

from _range_test.history import HistoryValidationError
from _range_test.history_range import complete_history_dates


def stream(dates, commodity=1):
    return {
        "resolved": True,
        "issues": [],
        "intervals": [
            {
                "start_utc": d.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "duration_seconds": 3600 if commodity == 1 else 86400,
                "raw_value": 1200,
                "power_of_ten_multiplier": 0,
                "unit_of_measure": 72 if commodity == 1 else 169,
                "accepted_revision_id": 1,
            }
            for d in dates
        ],
    }


class HistoryRangeTests(unittest.TestCase):
    def test_complete_local_range(self):
        first = datetime(2025, 9, 7, 7, tzinfo=timezone.utc)
        last = datetime(2026, 10, 7, 6, tzinfo=timezone.utc)
        self.assertEqual(
            tuple(map(str, complete_history_dates(
                stream([first, last]), 1, "America/Los_Angeles"
            ))),
            ("2025-09-07", "2026-10-06"),
        )

    def test_gas_reporting_dates(self):
        days = [
            datetime(2025, 9, 8, 6, 59, tzinfo=timezone.utc),
            datetime(2026, 10, 7, 6, 59, tzinfo=timezone.utc),
        ]
        self.assertEqual(
            tuple(map(str, complete_history_dates(
                stream(days, 7), 7, "America/Los_Angeles"
            ))),
            ("2025-09-07", "2026-10-06"),
        )

    def test_unresolved_rejected(self):
        data = stream([])
        data["resolved"] = False
        with self.assertRaises(HistoryValidationError):
            complete_history_dates(data, 1, "UTC")

    def test_empty_rejected(self):
        with self.assertRaises(HistoryValidationError):
            complete_history_dates(stream([]), 1, "UTC")

    def test_more_than_441_days_rejected(self):
        first = datetime(2025, 1, 1, tzinfo=timezone.utc)
        last = first + timedelta(days=441)
        with self.assertRaises(HistoryValidationError):
            complete_history_dates(stream([first, last]), 1, "UTC")


if __name__ == "__main__":
    unittest.main()
