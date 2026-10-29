# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Prevent unsafe HA scheduler callbacks and stale listener cleanup."""

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = (
    ROOT / "custom_components" / "energy_usage"
    / "statistics_sync_schedule.py"
)


class SchedulerThreadSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = MODULE.read_text()
        cls.tree = ast.parse(cls.source)
        cls.cls = next(
            node for node in cls.tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "AutomaticSync"
        )

    def method(self, name):
        return next(
            node for node in self.cls.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == name
        )

    def test_trigger_is_an_event_loop_callback(self):
        method = self.method("trigger")
        self.assertTrue(any(
            isinstance(node, ast.Name) and node.id == "callback"
            for node in method.decorator_list
        ))
        self.assertIn("hass.async_create_task", self.source)

    def test_startup_listener_is_an_event_loop_callback(self):
        start = self.method("start")
        nested = next(
            node for node in ast.walk(start)
            if isinstance(node, ast.FunctionDef)
            and node.name == "on_started"
        )
        self.assertTrue(any(
            isinstance(node, ast.Name) and node.id == "callback"
            for node in nested.decorator_list
        ))

    def test_one_shot_subscription_not_in_generic_list(self):
        start = ast.get_source_segment(self.source, self.method("start"))
        self.assertIn("self._startup_unsubscribe = (", start)
        self.assertIn("self._startup_unsubscribe = None", start)
        self.assertNotIn(
            "self._unsubscribers.append(\n"
            "                    self.hass.bus.async_listen_once", start
        )

    def test_stop_only_unsubscribes_pending_startup_listener(self):
        stop = ast.get_source_segment(self.source, self.method("stop"))
        self.assertIn("if self._startup_unsubscribe is not None:", stop)
        self.assertIn("self._startup_unsubscribe()", stop)
        self.assertIn("self._startup_unsubscribe = None", stop)


if __name__ == "__main__":
    unittest.main()
