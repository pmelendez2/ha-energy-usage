# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Static security and wiring checks for the authenticated upload view."""

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "energy_usage"


class UtilityUploadContractTests(unittest.TestCase):
    def test_view_is_authenticated_and_bounded(self):
        source = (COMPONENT / "utility_upload.py").read_text()
        ast.parse(source)
        self.assertIn('requires_auth = True', source)
        self.assertIn('/api/energy-usage/utility-upload', source)
        self.assertIn('MAX_XML_BYTES = 8 * 1024 * 1024', source)
        self.assertIn('iter_chunked(65536)', source)
        self.assertIn('api.import_green_button(source_id, xml)', source)
        self.assertIn('runtime_for_entry(entry)', source)
        self.assertIn('"synchronized": False', source)

    def test_registered_at_integration_setup(self):
        source = (COMPONENT / "__init__.py").read_text()
        ast.parse(source)
        self.assertIn('hass.http.register_view(UtilityUploadView(hass))', source)


if __name__ == "__main__":
    unittest.main()
