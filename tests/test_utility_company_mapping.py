# SPDX-License-Identifier: MIT
"""Utility-company selection never exposes acquisition-source labels."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / 'custom_components/energy_usage/www/energy-usage-utility-card.js'


class UtilityCompanyMappingTests(unittest.TestCase):
    def test_company_label_and_single_company_behavior(self):
        code = CARD.read_text()
        self.assertIn('option.textContent = sources[0].utility_company', code)
        self.assertIn('sourceLabel.hidden = sourceSelect.options.length <= 1', code)
        self.assertIn('Download data from ${utilityName}', code)
        self.assertIn('option.dataset.utilityId = utilityId', code)
        self.assertIn('if (sources.length !== 1)', code)
        self.assertIn('multiple acquisition sources', code)

    def test_website_security(self):
        code = CARD.read_text()
        self.assertEqual(
            code.count('["http:", "https:"].includes(url.protocol)'), 2
        )
        self.assertIn('url.username || url.password', code)
        self.assertIn('download.rel = "noopener noreferrer"', code)
        self.assertIn('utility_websites', code)
