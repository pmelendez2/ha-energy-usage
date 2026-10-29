# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Recorder completion barrier and read-back regression tests."""

import asyncio
import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType

# Resolve modules only when a test executes. Existing legacy tests reload
# package modules during discovery; eager importing here breaks exception identity.

STAMP = datetime(2026, 10, 6, tzinfo=timezone.utc)
ID = "energy_usage:electricity_meter_1"
ROWS = [{"start": STAMP, "state": 1.0, "sum": 1.0}]


class RecorderCompletionTests(unittest.TestCase):
    def setUp(self):
        from custom_components.energy_usage.statistics_sync_plan import (
            StatisticsSyncError,
        )
        from custom_components.energy_usage.statistics_sync_completion import (
            verify_after_recorder_commit,
        )
        self.verify = verify_after_recorder_commit
        self.error = self.verify.__globals__["StatisticsSyncError"]

    def test_waits_for_barrier_before_read(self):
        events = []

        async def barrier():
            events.append("commit")

        async def read(*args):
            events.append("read")
            return ROWS

        result = asyncio.run(self.verify(
            None, ID, ROWS, wait_for_commit=barrier,
            read_statistics=read,
        ))
        self.assertEqual(events, ["commit", "read"])
        self.assertEqual(result.observations, 1)

    def test_detects_missing_persisted_observation(self):
        async def barrier():
            return None

        async def read(*args):
            return []

        with self.assertRaises(self.error):
            asyncio.run(self.verify(
                None, ID, ROWS, wait_for_commit=barrier,
                read_statistics=read,
            ))

    def test_barrier_failure_propagates_without_read(self):
        async def barrier():
            raise RuntimeError("Recorder failed")

        async def read(*args):
            self.fail("Must not read before commit")

        with self.assertRaisesRegex(RuntimeError, "Recorder failed"):
            asyncio.run(self.verify(
                None, ID, ROWS, wait_for_commit=barrier,
                read_statistics=read,
            ))

    def test_rejects_unverified_barrier(self):
        with self.assertRaises(self.error):
            asyncio.run(self.verify(
                None, ID, ROWS, wait_for_commit=None,
            ))


if __name__ == "__main__":
    unittest.main()
