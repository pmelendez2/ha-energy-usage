# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Static contract tests for the explicit synchronization action."""

import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "custom_components/energy_usage/statistics_sync_service.py"
PATCH = ROOT / "scripts/apply-sync-service.py"


class SyncServiceWiringTests(unittest.TestCase):
    def test_action_requires_meter_id(self):
        tree = ast.parse(SRC.read_text())
        funcs = {n.name for n in tree.body if isinstance(n, ast.AsyncFunctionDef)}
        self.assertIn("async_register_sync_service", funcs)
        self.assertIn("sync_one", funcs)
        self.assertIn("SERVICE", SRC.read_text())
        self.assertIn('"sync_usage"', SRC.read_text())

    def test_registration_is_not_automatic_sync(self):
        src = SRC.read_text()
        self.assertIn("async_register(", src)
        self.assertNotIn("await sync_one(hass, entry", src.split(
            "async def async_register_sync_service", 1)[1].split(
            "async def handle", 1)[0])

    def test_patcher_checks_known_anchors(self):
        source = PATCH.read_text()
        self.assertIn("source.count(anchor) != 1", source)
        self.assertIn("async_register_sync_service", source)
        self.assertIn("SYNC_SERVICE", source)


if __name__ == "__main__":
    unittest.main()
