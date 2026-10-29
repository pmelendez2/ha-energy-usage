# SPDX-License-Identifier: MIT
"""Regression tests for synchronization action form definitions."""

import importlib.util
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "fix-sync-ui.py"
SPEC = importlib.util.spec_from_file_location("fix_sync_ui", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TestSyncUI(unittest.TestCase):
    def test_sync_usage_has_meter_id_selector(self):
        source = (ROOT / "custom_components/energy_usage/services.yaml")
        data = yaml.safe_load(source.read_text())
        self.assertIn("sync_usage", data)
        field = data["sync_usage"]["fields"]["meter_id"]
        self.assertTrue(field["required"])
        self.assertEqual(field["selector"]["number"]["min"], 1)
        self.assertEqual(field["selector"]["number"]["mode"], "box")

    def test_patch_is_idempotent(self):
        source = (ROOT / "custom_components/energy_usage/services.yaml")
        self.assertEqual(MODULE.apply(source.read_text()), source.read_text())

    def test_patch_preserves_existing_services(self):
        original = "sync_preflight:\n  fields:\n    meter_id:\n      required: true\n"
        updated = MODULE.apply(original)
        self.assertEqual(yaml.safe_load(updated)["sync_preflight"],
                         yaml.safe_load(original)["sync_preflight"])


if __name__ == "__main__":
    unittest.main()
