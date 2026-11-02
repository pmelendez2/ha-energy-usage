# SPDX-License-Identifier: MIT
"""Regression checks for single-company display and import summaries."""
from pathlib import Path
import subprocess
import unittest

CARD = (Path(__file__).resolve().parents[1] /
        "custom_components/energy_usage/www/energy-usage-utility-card.js")


class UtilityCardRefinementTests(unittest.TestCase):
    def test_selector_hidden_even_with_display_block_style(self):
        js = CARD.read_text(encoding="utf-8")
        self.assertIn("[hidden] { display: none !important; }", js)
        self.assertIn("sourceLabel.hidden = sourceSelect.options.length <= 1", js)

    def test_ambiguous_source_fails_closed(self):
        js = CARD.read_text(encoding="utf-8")
        self.assertIn("if (sources.length !== 1)", js)
        self.assertIn("multiple acquisition sources", js)
        self.assertNotIn("if (sources.length !== 1) continue;", js)

    def test_human_readable_summary_and_meter_scope(self):
        js = CARD.read_text(encoding="utf-8")
        self.assertIn("function formatImportSummary(outcomes, synchronized)", js)
        self.assertIn("Observations checked:", js)
        self.assertIn("Already recorded:", js)
        self.assertIn("New observations accepted:", js)
        self.assertIn("Recorder meters synchronized:", js)
        self.assertIn("do not identify the XML file's commodity", js)
        self.assertNotIn("JSON.stringify(outcomes, null, 2)", js)

    def test_javascript_syntax(self):
        subprocess.run(["node", "--check", str(CARD)], check=True)


if __name__ == "__main__":
    unittest.main()
