# SPDX-License-Identifier: MIT
"""Check the dashboard upload card and authenticated API contract."""
from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "custom_components" / "energy_usage"


class UtilityCardTests(unittest.TestCase):
    def test_upload_supports_json_and_authentication(self):
        text = (BASE / "utility_upload.py").read_text()
        ast.parse(text)
        self.assertIn('requires_auth = True', text)
        self.assertIn('base64.b64decode(encoded, validate=True)', text)
        self.assertIn('MAX_XML_BYTES = 8 * 1024 * 1024', text)
        self.assertIn('"synchronized": False', text)

    def test_card_uses_authenticated_ha_api(self):
        text = (BASE / "www/energy-usage-utility-card.js").read_text()
        self.assertIn('this._hass.callApi(', text)
        self.assertIn('"energy-usage/utility-upload"', text)
        self.assertIn('"Import XML files"', text)
        self.assertIn('"noopener noreferrer"', text)
        self.assertNotIn('api_token', text)

    def test_folder_selection_and_batch_review(self):
        text = (BASE / "www/energy-usage-utility-card.js").read_text()
        for expected in (
            'input.multiple = true',
            '"webkitdirectory"',
            '"Select all"',
            '"Clear selection"',
            'file.name.toLowerCase().endsWith(".xml")',
            'pendingResources.push({resourceId, meterId: null})',
            'sourceSelect.value',
            '"energy-usage/utility-upload"',
        ):
            self.assertIn(expected, text)

    def test_public_urls_are_hyphenated(self):
        text = (BASE / "__init__.py").read_text()
        self.assertIn('/energy-usage/energy-usage-explorer.js', text)
        self.assertIn('LEGACY_EXPLORER_URL', text)
        self.assertIn('/energy-usage/energy-usage-utility-card.js', text)


if __name__ == "__main__":
    unittest.main()
