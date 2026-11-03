# SPDX-License-Identifier: MIT
"""ADR-0003 fail-closed commodity-aware mapping UI contracts."""

from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "custom_components/energy_usage/www/energy-usage-utility-card.js"


class UtilityCommodityTests(unittest.TestCase):
    def test_resource_commodity_required(self):
        source = CARD.read_text()
        self.assertIn("const commodity = state.commodity;", source)
        self.assertIn("Resource commodity unavailable", source)
        self.assertIn("Conflicting resource commodity", source)
        self.assertIn("Confirmed meter has incompatible commodity", source)

    def test_meter_options_filtered_to_canonical_commodity(self):
        source = CARD.read_text()
        self.assertIn("Number(meter.commodity) === item.commodity", source)
        self.assertIn('"Electricity usage"', source)
        self.assertIn('"Natural gas usage"', source)
        self.assertIn("label.title = `Reading resource", source)

    def test_clear_files_removes_candidates_and_filenames(self):
        source = CARD.read_text()
        self.assertIn('clear.textContent = "Clear files"', source)
        self.assertIn("candidates = [];", source)
        self.assertIn("list.replaceChildren();", source)
        self.assertIn('status.textContent = "No XML files selected."', source)

    def test_import_completion_reenables_mapping_controls(self):
        source = CARD.read_text()
        self.assertIn("busy = false;\n        renderMappings();", source)

    def test_syntax(self):
        subprocess.run(["node", "--check", str(CARD)], check=True)


if __name__ == "__main__":
    unittest.main()
