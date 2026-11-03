# SPDX-License-Identifier: MIT
"""ADR-0003 contracts for automatic synchronization after association."""

from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "custom_components/energy_usage/www/energy-usage-utility-card.js"
UPLOAD = ROOT / "custom_components/energy_usage/utility_upload.py"


class UtilityAutoSyncTests(unittest.TestCase):
    def test_confirmed_mappings_start_sync_without_click(self):
        source = CARD.read_text()
        self.assertIn("void submitMappings(true);", source)
        self.assertIn("item.confirmed &&", source)
        self.assertIn("!autoAttempted.has(item.resourceId)", source)
        self.assertIn("const autoAttempted = new Set();", source)

    def test_unknown_meters_require_explicit_confirmation(self):
        source = CARD.read_text()

        self.assertIn(
            'confirm.textContent = "Confirm meters and finish"',
            source,
        )
        self.assertIn(
            'associationWarning.setAttribute("role", "alert")',
            source,
        )
        self.assertIn(
            "associationWarning.hidden = !needsConfirmation",
            source,
        )
        self.assertIn(
            "pendingResources.some(item => !item.confirmed)",
            source,
        )
        self.assertIn("!item.confirmed", source)
        self.assertIn("unresolved.some(item => !item.meterId)", source)
        self.assertIn("submitMappings(false)", source)

    def test_progress_and_failure_recovery_are_visible(self):
        source = CARD.read_text()
        self.assertIn("Synchronizing Home Assistant Recorder", source)
        self.assertIn("Synchronization completed successfully", source)
        self.assertIn('status.setAttribute("aria-live", "polite")', source)
        self.assertIn('retry.dataset.available = "1"', source)

    def test_backend_remains_scoped_to_explicit_resource_ids(self):
        source = UPLOAD.read_text()
        self.assertIn("if not set(meter_ids) <= allowed:", source)
        self.assertIn("async def _associate(self, entry, payload):", source)
        self.assertIn("return await self._associate(entry, payload)", source)

    def test_javascript_syntax(self):
        subprocess.run(["node", "--check", str(CARD)], check=True)


if __name__ == "__main__":
    unittest.main()
