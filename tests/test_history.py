# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Project Contributors
"""Unit tests for history normalization and safety gates."""

import unittest
from decimal import Decimal

# Load pure normalization without importing Home Assistant's __init__.py.
import importlib.util
from pathlib import Path

HISTORY_PATH = (Path(__file__).resolve().parents[1]
                / "custom_components/energy_usage/history.py")
spec = importlib.util.spec_from_file_location(
    "energy_usage_history_unit", HISTORY_PATH
)
module = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = module
spec.loader.exec_module(module)
HistoryValidationError = module.HistoryValidationError
normalize_stream = module.normalize_stream


def sample(**changes):
    """Create a synthetic interval without customer data."""
    interval = {
        "start_utc": "2026-01-01T08:00:00Z",
        "duration_seconds": 3600,
        "raw_value": 1000,
        "power_of_ten_multiplier": 0,
        "unit_of_measure": 72,
        "accepted_revision_id": 13,
    }
    interval.update(changes)
    return interval


class NormalizationTests(unittest.TestCase):
    """Verify fail-closed behavior for historical usage inputs."""

    def test_electricity_wh_to_kwh(self):
        rows = normalize_stream(
            {"resolved": True, "issues": [], "intervals": [sample()]},
            commodity=1,
        )
        self.assertEqual(rows[0].value, Decimal("1.000"))
        self.assertEqual(rows[0].unit, "kWh")
        self.assertEqual(rows[0].revision_id, 13)

    def test_gas_multiplier_preserved(self):
        row = sample(
            unit_of_measure=169,
            power_of_ten_multiplier=-3,
            raw_value=1250,
            duration_seconds=86400,
            start_utc="2026-01-01T07:59:00Z",
        )
        rows = normalize_stream(
            {"resolved": True, "issues": [], "intervals": [row]},
            commodity=7,
        )
        self.assertEqual(rows[0].value, Decimal("1.250"))
        self.assertEqual(rows[0].unit, "therm")

    def test_unresolved_rejected(self):
        with self.assertRaises(HistoryValidationError):
            normalize_stream(
                {"resolved": False, "issues": [], "intervals": []},
                commodity=1,
            )

    def test_duplicates_rejected(self):
        with self.assertRaises(HistoryValidationError):
            normalize_stream(
                {"resolved": True, "issues": [],
                 "intervals": [sample(), sample()]},
                commodity=1,
            )

    def test_wrong_unit_rejected(self):
        with self.assertRaises(HistoryValidationError):
            normalize_stream(
                {"resolved": True, "issues": [],
                 "intervals": [sample(unit_of_measure=169)]},
                commodity=1,
            )

    def test_overlapping_intervals_rejected(self):
        with self.assertRaises(HistoryValidationError):
            normalize_stream(
                {"resolved": True, "issues": [], "intervals": [
                    sample(),
                    sample(start_utc="2026-01-01T08:30:00Z"),
                ]},
                commodity=1,
            )


if __name__ == "__main__":
    unittest.main()
