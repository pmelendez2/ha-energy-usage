# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Verify initial-import reservations and safe retry boundaries."""

import importlib.util
from pathlib import Path
import unittest


SOURCE = (
    Path(__file__).resolve().parents[1]
    / "custom_components/energy_usage/history_import_guard.py"
)
spec = importlib.util.spec_from_file_location("_import_guard_test", SOURCE)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class InitialImportGuardTests(unittest.TestCase):
    def setUp(self):
        self.pending = set()
        self.key = ("entry-one", 1)

    def test_empty_series_allows_first_attempt(self):
        guard.check_initial_import(self.pending, self.key, False)
        self.assertEqual(self.pending, set())

    def test_pending_write_never_allows_duplicate(self):
        self.pending.add(self.key)
        with self.assertRaisesRegex(
            guard.InitialImportBlocked, "still unconfirmed"
        ):
            guard.check_initial_import(self.pending, self.key, False)
        self.assertIn(self.key, self.pending)

    def test_confirmed_history_clears_reservation(self):
        self.pending.add(self.key)
        with self.assertRaisesRegex(
            guard.InitialImportBlocked, "History already exists"
        ):
            guard.check_initial_import(self.pending, self.key, True)
        self.assertNotIn(self.key, self.pending)

    def test_existing_history_blocks_without_pending_write(self):
        with self.assertRaises(guard.InitialImportBlocked):
            guard.check_initial_import(self.pending, self.key, True)

    def test_other_meter_reservation_is_independent(self):
        self.pending.add(self.key)
        guard.check_initial_import(
            self.pending, ("entry-one", 2), False
        )

    def test_restart_with_no_history_allows_safe_retry(self):
        self.pending.add(self.key)
        # Process-local reservations are absent after HA restarts.
        guard.check_initial_import(set(), self.key, False)


if __name__ == "__main__":
    unittest.main()
