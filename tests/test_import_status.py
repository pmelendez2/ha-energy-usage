# SPDX-License-Identifier: MIT
"""Test status transitions independently of Home Assistant Core."""

import importlib.util
from pathlib import Path
import unittest


SOURCE = (
    Path(__file__).resolve().parents[1]
    / "custom_components/energy_usage/import_status.py"
)
spec = importlib.util.spec_from_file_location("_import_status_test", SOURCE)
status = importlib.util.module_from_spec(spec)
spec.loader.exec_module(status)


class ImportStatusTests(unittest.TestCase):
    def setUp(self):
        self.key = status.key_for("entry-test", 11)
        status.clear_entry("entry-test")

    def tearDown(self):
        status.clear_entry("entry-test")

    def test_unseen_meter_without_rows(self):
        state, attempt = status.snapshot(self.key, False)
        self.assertEqual(state, "Not imported")
        self.assertEqual(attempt, {})

    def test_start_and_queue_are_not_success(self):
        status.started(self.key)
        self.assertEqual(status.snapshot(self.key, False)[0], "Importing")
        status.queued(self.key)
        state, attempt = status.snapshot(self.key, False)
        self.assertEqual(state, "Importing")
        self.assertEqual(attempt["last_attempt"], "Awaiting Recorder")
        self.assertIsNone(attempt["last_success_at"])

    def test_persisted_readback_confirms_success(self):
        status.started(self.key)
        status.queued(self.key)
        state, attempt = status.snapshot(self.key, True)
        self.assertEqual(state, "Imported")
        self.assertEqual(attempt["last_attempt"], "Succeeded")
        self.assertIsNotNone(attempt["last_success_at"])

    def test_failure_remains_visible(self):
        status.started(self.key)
        status.failed(self.key, "Server unreachable")
        state, attempt = status.snapshot(self.key, False)
        self.assertEqual(state, "Failed")
        self.assertEqual(attempt["last_error"], "Server unreachable")

    def test_duplicate_failure_does_not_hide_existing_rows(self):
        status.started(self.key)
        status.failed(self.key, "History already exists")
        state, attempt = status.snapshot(self.key, True)
        self.assertEqual(state, "Imported")
        self.assertEqual(attempt["last_attempt"], "Failed")

    def test_previous_success_survives_failed_retry(self):
        status.started(self.key)
        status.queued(self.key)
        status.snapshot(self.key, True)
        status.started(self.key)
        status.failed(self.key, "History already exists")
        state, attempt = status.snapshot(self.key, True)
        self.assertEqual(state, "Imported")
        self.assertIsNotNone(attempt["last_success_at"])

    def test_isolated_meters_and_unload(self):
        status.started(self.key)
        self.assertEqual(
            status.snapshot(status.key_for("other", 11), False)[0],
            "Not imported",
        )
        status.clear_entry("entry-test")
        self.assertEqual(status.snapshot(self.key, False)[0], "Not imported")

    def test_attempt_details_does_not_claim_success(self):
        status.started(self.key)
        status.queued(self.key)
        self.assertEqual(
            status.attempt_details(self.key)["last_attempt"],
            "Awaiting Recorder",
        )
        self.assertIsNone(
            status.attempt_details(self.key)["last_success_at"]
        )


if __name__ == "__main__":
    unittest.main()
