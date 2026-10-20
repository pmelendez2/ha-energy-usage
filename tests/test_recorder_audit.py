# SPDX-License-Identifier: MIT
"""Read-only audit regression tests for Recorder drift and safety gates."""

import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = "custom_components.energy_usage"
for name, filename in (
    (PKG, None),
    (PKG + ".statistics_plan", "statistics_plan.py"),
    (PKG + ".statistics_preview", "statistics_preview.py"),
    (PKG + ".recorder_bridge", "recorder_bridge.py"),
    (PKG + ".recorder_audit", "recorder_audit.py"),
):
    if name not in sys.modules:
        if filename is None:
            module = types.ModuleType(name)
            module.__path__ = [str(ROOT / "custom_components/energy_usage")]
        else:
            spec = importlib.util.spec_from_file_location(
                name, ROOT / "custom_components/energy_usage" / filename
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
        sys.modules[name] = module

from custom_components.energy_usage.recorder_audit import (
    audit_recorder_series,
)
from custom_components.energy_usage.recorder_bridge import (
    RecorderImportBatch, RecorderSafetyError,
)

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
ID = "energy_usage:electricity_meter_1"
META = {"statistic_id": ID, "source": "energy_usage"}


def batch():
    return RecorderImportBatch(ID, dict(META), (
        {"start": T0, "sum": 1.0},
        {"start": T0 + timedelta(hours=2), "sum": 3.0},
    ))


def stored():
    return [dict(row) for row in batch().rows]


class RecorderAuditTests(unittest.TestCase):
    def audit(self, rows, **kwargs):
        return audit_recorder_series(
            batch(), rows, complete_readback=True, **kwargs
        )

    def test_identical_series(self):
        self.assertTrue(self.audit(stored()).matches)

    def test_out_of_order_readback(self):
        self.assertTrue(self.audit(list(reversed(stored()))).matches)

    def test_epoch_readback(self):
        rows = stored()
        for row in rows:
            row["start"] = row["start"].timestamp()
        self.assertTrue(self.audit(rows).matches)

    def test_missing_row_is_not_synthesized(self):
        audit = self.audit(stored()[:1])
        self.assertEqual(audit.missing, (T0 + timedelta(hours=2),))
        self.assertFalse(audit.matches)

    def test_unexpected_gap_row_is_detected(self):
        rows = stored() + [{"start": T0 + timedelta(hours=1), "sum": 2}]
        self.assertEqual(self.audit(rows).unexpected,
                         (T0 + timedelta(hours=1),))

    def test_old_correction_drift(self):
        rows = stored()
        rows[1]["sum"] = 2.5
        self.assertEqual(self.audit(rows).mismatched,
                         (T0 + timedelta(hours=2),))

    def test_duplicate_readback_rejected(self):
        with self.assertRaises(RecorderSafetyError):
            self.audit(stored() + stored()[:1])

    def test_incomplete_readback_rejected(self):
        with self.assertRaises(RecorderSafetyError):
            audit_recorder_series(batch(), [], complete_readback=False)

    def test_unowned_statistic_rejected(self):
        altered = RecorderImportBatch("other:meter_1", META, batch().rows)
        with self.assertRaises(RecorderSafetyError):
            audit_recorder_series(altered, stored(), complete_readback=True)

    def test_invalid_number_rejected(self):
        rows = stored()
        rows[0]["sum"] = float("nan")
        with self.assertRaises(RecorderSafetyError):
            self.audit(rows)

    def test_naive_timestamp_rejected(self):
        rows = stored()
        rows[0]["start"] = T0.replace(tzinfo=None)
        with self.assertRaises(RecorderSafetyError):
            self.audit(rows)

    def test_tolerance(self):
        rows = stored()
        rows[0]["sum"] += 1e-9
        self.assertTrue(self.audit(rows).matches)
        self.assertFalse(self.audit(rows, tolerance=0).matches)
