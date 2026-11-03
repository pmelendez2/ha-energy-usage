# SPDX-License-Identifier: MIT
"""Upload authorization and source-discovery contract checks."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "energy_usage"


class UploadSecurityTests(unittest.TestCase):
    def test_admin_and_source_checks(self):
        source = (COMPONENT / "utility_upload.py").read_text()
        ast.parse(source)
        self.assertIn('user.is_admin', source)
        self.assertIn('async def get(self, request)', source)
        self.assertIn('api.acquisition_sources()', source)
        self.assertIn('Unknown acquisition source', source)
        self.assertIn('async with self._lock:', source)
        self.assertIn('iter_chunked(65536)', source)
        self.assertIn('sync_only', source)

    def test_client_and_card_discovery(self):
        api = (COMPONENT / "api.py").read_text()
        card = (COMPONENT / "www/energy-usage-utility-card.js").read_text()
        self.assertIn('/v1/acquisition-sources', api)
        self.assertIn('"GET", "energy-usage/utility-upload"', card)
        self.assertIn('sourceSelect.value', card)
        self.assertIn(
            '"Retry association and Recorder synchronization"', card
        )


if __name__ == "__main__":
    unittest.main()
