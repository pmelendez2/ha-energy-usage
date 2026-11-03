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
        self.assertIn(
            "function formatImportSummary(outcomes, synchronized)",
            js,
        )
        self.assertIn("Results for each XML file:", js)
        self.assertIn("Already imported — no changes needed.", js)
        self.assertIn("usage reading(s) added or updated.", js)
        self.assertIn("usage data is up to date.", js)
        self.assertIn("No usage readings were processed", js)
        self.assertIn("Home Assistant history:", js)
        self.assertIn('imported.already_imported', js)
        self.assertIn(
            "Retry association and Recorder synchronization",
            js,
        )
        self.assertIn(
            "retry.hidden = !retry.dataset.available",
            js,
        )
        self.assertNotIn("JSON.stringify(outcomes, null, 2)", js)

    def test_javascript_syntax(self):
        subprocess.run(["node", "--check", str(CARD)], check=True)

    def test_import_summary_values(self):
        script = CARD.parents[3] / "tests/test-utility-import-summary.cjs"
        subprocess.run(["node", str(script)], check=True)


if __name__ == "__main__":
    unittest.main()
