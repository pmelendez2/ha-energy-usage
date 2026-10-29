# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Contract coverage for user configurable scheduling options."""
import ast
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "custom_components/energy_usage"


class SyncOptionsTests(unittest.TestCase):
    def test_defaults_and_choices(self):
        tree = ast.parse((BASE / "statistics_sync_settings.py").read_text())
        values = {}
        for node in tree.body:
            if isinstance(node, ast.Assign):
                if (len(node.targets) == 1
                        and isinstance(node.targets[0], ast.Name)):
                    name = node.targets[0].id
                    if name in ("DEFAULT_SYNC_HOURS", "DEFAULT_SYNC_STARTUP",
                                "SYNC_INTERVAL_CHOICES"):
                        values[name] = ast.literal_eval(node.value)
        self.assertEqual(values["DEFAULT_SYNC_HOURS"], 24)
        self.assertTrue(values["DEFAULT_SYNC_STARTUP"])
        self.assertEqual(set(values["SYNC_INTERVAL_CHOICES"]),
                         {6, 12, 24, 168})

    def test_options_flow_exists(self):
        source = (BASE / "config_flow.py").read_text()
        self.assertIn("async_get_options_flow", source)
        self.assertIn("class EnergyUsageOptionsFlow", source)
        self.assertIn("self.config_entry.options", source)
        self.assertIn("SYNC_INTERVAL_CHOICES", source)

    def test_saved_options_reload_entry(self):
        source = (BASE / "__init__.py").read_text()
        self.assertIn("entry.add_update_listener", source)
        self.assertIn("async_reload(", source)
        self.assertIn("changed_entry.entry_id", source)
        self.assertIn("entry.async_on_unload", source)

    def test_customer_translations_match(self):
        strings = json.loads((BASE / "strings.json").read_text())
        english = json.loads((BASE / "translations/en.json").read_text())
        self.assertEqual(strings, english)
        fields = strings["options"]["step"]["init"]["data"]
        self.assertIn("sync_interval_hours", fields)
        self.assertIn("sync_on_startup", fields)


if __name__ == "__main__":
    unittest.main()
