# SPDX-License-Identifier: MIT
"""Isolated tests for guarded Recorder initial import and read-back."""

import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = "custom_components.energy_usage"
for name, path in (
    (PKG, None),
    (PKG + ".statistics_plan", "statistics_plan.py"),
    (PKG + ".statistics_preview", "statistics_preview.py"),
    (PKG + ".recorder_bridge", "recorder_bridge.py"),
):
    if path is None:
        pkg = types.ModuleType(name)
        pkg.__path__ = [str(ROOT / "custom_components/energy_usage")]
        sys.modules.setdefault(name, pkg)
    else:
        if name not in sys.modules:
            spec = importlib.util.spec_from_file_location(
                name, ROOT / "custom_components/energy_usage" / path
            )
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)

from custom_components.energy_usage.recorder_bridge import (
    RecorderSafetyError, prepare_initial_import, verify_import,
)
from custom_components.energy_usage.statistics_preview import (
    StatisticsPreview,
)

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
META = {
    "statistic_id": "energy_usage:electricity_meter_1",
    "source": "energy_usage", "unit_of_measurement": "kWh",
    "unit_class": "energy", "has_sum": True, "mean_type": 0,
    "name": "Electricity meter 1",
}


def preview(*, incomplete=(), rows=None, meta=None):
    return StatisticsPreview(
        "energy_usage:electricity_meter_1",
        dict(META if meta is None else meta),
        tuple(rows if rows is not None else [
            {"start": T0, "sum": 2.0},
            {"start": T0 + timedelta(hours=1), "sum": 3.5},
        ]), tuple(incomplete),
    )


class RecorderBridgeTests(unittest.TestCase):
    def test_explicit_approval_required(self):
        with self.assertRaises(RecorderSafetyError):
            prepare_initial_import(preview(), [])

    def test_existing_series_blocks_import(self):
        with self.assertRaises(RecorderSafetyError):
            prepare_initial_import(preview(), [{"start": T0}], confirmed=True)

    def test_incomplete_hours_block_unreviewed_import(self):
        with self.assertRaises(RecorderSafetyError):
            prepare_initial_import(preview(incomplete=(T0.isoformat(),)),
                                   [], confirmed=True)

    def test_successful_preview_is_immutable_batch(self):
        batch = prepare_initial_import(preview(), [], confirmed=True)
        self.assertEqual(batch.statistic_id, META["statistic_id"])
        self.assertEqual(len(batch.rows), 2)
        verify_import(batch, list(batch.rows))

    def test_wrong_source_rejected(self):
        meta = dict(META, source="recorder")
        with self.assertRaises(RecorderSafetyError):
            prepare_initial_import(preview(meta=meta), [], confirmed=True)

    def test_nonmonotonic_cumulative_rejected(self):
        rows = [{"start": T0, "sum": 3},
                {"start": T0 + timedelta(hours=1), "sum": 2}]
        with self.assertRaises(RecorderSafetyError):
            prepare_initial_import(preview(rows=rows), [], confirmed=True)

    def test_duplicate_timestamp_rejected(self):
        rows = [{"start": T0, "sum": 1},
                {"start": T0, "sum": 2}]
        with self.assertRaises(RecorderSafetyError):
            prepare_initial_import(preview(rows=rows), [], confirmed=True)

    def test_wrong_readback_detected(self):
        batch = prepare_initial_import(preview(), [], confirmed=True)
        with self.assertRaises(RecorderSafetyError):
            verify_import(batch, [{"start": T0, "sum": 5}])
        with self.assertRaises(RecorderSafetyError):
            verify_import(batch, [{"start": T0, "sum": 5},
                                  {"start": T0 + timedelta(hours=1),
                                   "sum": 3.5}])

    def test_epoch_readback_supported(self):
        batch = prepare_initial_import(preview(), [], confirmed=True)
        rows = [{"start": row["start"].timestamp(), "sum": row["sum"]}
                for row in batch.rows]
        verify_import(batch, rows)

    def test_empty_batch_rejected(self):
        with self.assertRaises(RecorderSafetyError):
            prepare_initial_import(preview(rows=[]), [], confirmed=True)


if __name__ == "__main__":
    unittest.main()
