# SPDX-License-Identifier: MIT
"""Contract checks for utility-specific website configuration."""
from pathlib import Path
import unittest

JS = (Path(__file__).resolve().parents[1] /
      "custom_components/energy_usage/www/energy-usage-utility-card.js")


class UtilityWebsiteEditorTests(unittest.TestCase):
    def test_company_named_url_fields(self):
        text = JS.read_text(encoding="utf-8")
        self.assertIn('`${name} download website (HTTP or HTTPS)`', text)
        self.assertIn('next.utility_websites = updated;', text)
        self.assertNotIn('utility_url', text)
        self.assertIn('"config-changed"', text)
        self.assertNotIn('Utility websites by company ID (JSON)', text)
        self.assertNotIn('Preferred acquisition source ID (optional)', text)

    def test_website_validation(self):
        text = JS.read_text(encoding="utf-8")
        self.assertIn('["http:", "https:"].includes(url.protocol)', text)
        self.assertIn('Enter a valid HTTP or HTTPS website URL', text)
        self.assertIn('input.placeholder = "http://utility.example/"', text)
        self.assertIn('url.username || url.password', text)
        self.assertIn('input.setCustomValidity(', text)
