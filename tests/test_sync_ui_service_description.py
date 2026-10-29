# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Regression tests for synchronization action form definitions."""

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SERVICES = ROOT / "custom_components/energy_usage/services.yaml"


class TestSyncUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = yaml.safe_load(SERVICES.read_text())

    def test_sync_usage_has_meter_id_selector(self):
        self.assertIn("sync_usage", self.data)
        field = self.data["sync_usage"]["fields"]["meter_id"]
        self.assertTrue(field["required"])
        self.assertEqual(field["selector"]["number"]["min"], 1)
        self.assertEqual(field["selector"]["number"]["mode"], "box")

    def test_preflight_service_is_preserved(self):
        self.assertIn("sync_preflight", self.data)

    def test_services_have_distinct_names(self):
        self.assertIn("sync_usage", self.data)
        self.assertIn("sync_preflight", self.data)
        self.assertNotEqual(
            self.data["sync_usage"],
            self.data["sync_preflight"],
        )


if __name__ == "__main__":
    unittest.main()
