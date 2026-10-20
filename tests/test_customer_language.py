# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Project Contributors
"""Tests for consistent customer-facing language and onboarding."""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CustomerLanguageTests(unittest.TestCase):
    """Confirm onboarding provides actionable credential guidance."""

    def test_translation_matches_strings(self):
        """English translation must match base customer text."""
        base = ROOT / "custom_components/energy_usage"
        source = json.loads((base / "strings.json").read_text())
        english = json.loads((base / "translations/en.json").read_text())
        self.assertEqual(source, english)

    def test_token_origin_documented(self):
        """Users must know where the API credential comes from."""
        path = ROOT / "custom_components/energy_usage/strings.json"
        form = json.loads(path.read_text())["config"]["step"]["user"]
        self.assertIn("created during Energy Ingest setup", form["description"])

    def test_internal_timezone_is_not_a_setup_requirement(self):
        """The setup form must not ask for an explicit UTC offset."""
        path = ROOT / "custom_components/energy_usage/strings.json"
        form = json.loads(path.read_text())["config"]["step"]["user"]
        self.assertNotIn("UTC", form["description"])

    def test_usage_date_range_defined(self):
        """Documentation must define the single canonical UI term."""
        text = (ROOT / "docs/TERMINOLOGY.md").read_text()
        self.assertIn("## Usage date range", text)
