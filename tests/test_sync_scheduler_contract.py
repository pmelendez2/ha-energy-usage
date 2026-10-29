# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Validate scheduled synchronization lifecycle without live Recorder."""

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCHEDULER = ROOT / "custom_components/energy_usage/statistics_sync_schedule.py"
INIT = ROOT / "custom_components/energy_usage/__init__.py"
SERVICE = ROOT / "custom_components/energy_usage/statistics_sync_service.py"


class SchedulerContractTests(unittest.TestCase):
    def test_scheduler_uses_entry_preferences(self):
        source = SCHEDULER.read_text()
        self.assertIn("sync_preferences(entry)", source)
        self.assertIn("timedelta(hours=self.interval_hours)", source)
        self.assertIn("if self.sync_on_startup:", source)

    def test_scheduler_refreshes_meters_and_isolates_failure(self):
        source = SCHEDULER.read_text()
        self.assertIn("await coordinator.async_refresh()", source)
        self.assertIn("await sync_one(", source)
        self.assertIn("retry next cycle", source)

    def test_scheduler_has_stop_and_startup_hooks(self):
        source = SCHEDULER.read_text()
        self.assertIn("EVENT_HOMEASSISTANT_STARTED", source)
        self.assertIn("async_track_time_interval", source)
        self.assertIn("await self._task", source)

    def test_runtime_is_shared(self):
        self.assertIn("def runtime_for_entry(", SERVICE.read_text())
        self.assertIn("runtime_for_entry(entry)", INIT.read_text())

    def test_scheduler_unloads(self):
        source = INIT.read_text()
        self.assertIn("start_automatic_sync(", source)
        self.assertIn("stop_automatic_sync(entry)", source)


if __name__ == "__main__":
    unittest.main()
