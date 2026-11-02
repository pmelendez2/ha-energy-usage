# SPDX-License-Identifier: MIT
"""Regression checks for the development utility card editor."""
from pathlib import Path
import unittest

JS = (Path(__file__).resolve().parents[1] /
      'custom_components/energy_usage/www/energy-usage-utility-card.js')


class UtilityCardEditorTests(unittest.TestCase):
    def test_editor_contract(self):
        text = JS.read_text(encoding='utf-8')
        for fragment in (
            'static getConfigElement()',
            'static getStubConfig()',
            'class EnergyUsageUtilityCardEditor',
            '"config-changed"',
            '"utility_url"',
            '"source_id"',
            '"https:"',
        ):
            self.assertIn(fragment, text)

    def test_initial_state_and_errors(self):
        text = JS.read_text(encoding='utf-8')
        for fragment in (
            'selectAll.disabled = true;',
            'clear.disabled = true;',
            'function utilityErrorMessage(error)',
            'utilityErrorMessage(error)',
            'sourceSelect.replaceChildren();',
            'count.textContent =',
        ):
            self.assertIn(fragment, text)
        self.assertNotIn('String(error.message || error)', text)


if __name__ == '__main__':
    unittest.main()
