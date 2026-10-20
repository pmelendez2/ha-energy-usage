# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Project Contributors
"""Check the shipped integration identity and manifest contract."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ROOT / "custom_components"


class PackageLayoutTests(unittest.TestCase):
    def test_one_domain(self):
        self.assertEqual(
            sorted(p.name for p in COMPONENTS.iterdir() if p.is_dir()),
            ["energy_usage"],
        )

    def test_manifest_identity(self):
        manifest = json.loads(
            (COMPONENTS / "energy_usage/manifest.json").read_text()
        )
        self.assertEqual(manifest["domain"], "energy_usage")
        self.assertTrue(manifest["config_flow"])
        self.assertEqual(manifest["name"], "Energy Usage")

    def test_config_strings_match_translation(self):
        root = COMPONENTS / "energy_usage"
        strings = json.loads((root / "strings.json").read_text())
        english = json.loads(
            (root / "translations/en.json").read_text()
        )
        self.assertEqual(strings, english)
