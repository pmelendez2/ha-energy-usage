# SPDX-License-Identifier: MIT
"""UI regression checks for utility-company and picker terminology."""
from pathlib import Path
import unittest

JS = (Path(__file__).resolve().parents[1] /
      "custom_components/energy_usage/www/energy-usage-utility-card.js")


class UtilityCardUsabilityTests(unittest.TestCase):
    def test_clear_labels_and_additive_selection(self):
        source = JS.read_text(encoding="utf-8")
        for expected in (
            '"Utility Company"',
            '"Choose Files"',
            '"Choose Folder"',
            'const existing = new Set(',
            'candidates.push({file, checked: true})',
            'selected().length === candidates.length',
            'clear.disabled = busy || candidates.length === 0',
        ):
            self.assertIn(expected, source)
        self.assertNotIn('"Acquisition source"', source)
        self.assertNotIn('"Select an acquisition source."', source)


if __name__ == "__main__":
    unittest.main()
