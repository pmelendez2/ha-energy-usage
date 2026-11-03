# SPDX-License-Identifier: MIT
"""Regression contract for guided physical-meter association."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "custom_components/energy_usage"


class GuidedMeterWorkflowTests(unittest.TestCase):
    def test_import_cannot_trigger_unscoped_recorder_sync(self):
        source = (BASE / "utility_upload.py").read_text()
        ast.parse(source)
        self.assertIn("Unscoped Recorder synchronization is disabled", source)
        self.assertIn("Associate imported resources", source)
        self.assertIn("return await self._associate(entry, payload)", source)
        self.assertIn("if not set(meter_ids) <= allowed:", source)
        self.assertIn("await api.associate_resource(", source)
        self.assertIn("await self._sync(entry, meter_ids)", source)
        self.assertNotIn("await self._sync(entry)", source)

    def test_ui_requires_explicit_selection_for_each_resource(self):
        source = (BASE / "www/energy-usage-utility-card.js").read_text()
        self.assertIn(
            'confirm.textContent = "Confirm meters and finish"',
            source,
        )
        self.assertIn("void submitMappings(true);", source)
        self.assertIn("Select physical meter", source)
        self.assertIn("pendingResources.some(item => !item.meterId)", source)
        self.assertIn("resource_ids", source)
        self.assertIn("associations: batch.map", source)
        self.assertNotIn("sync: i === queue.length - 1", source)
        self.assertNotIn("{sync_only: true}", source)

    def test_recovery_and_backend_lookup_are_required(self):
        source = (BASE / "utility_upload.py").read_text()
        self.assertIn('Store(hass, 1, "energy_usage_pending_imports")', source)
        self.assertIn('await self._remember(entry, result["resource_ids"])', source)
        self.assertIn('await self._forget(entry, resource_ids)', source)
        self.assertIn('await self._lookup(entry, resource_ids)', source)
        self.assertIn('"conflicting_resource_ids": conflicts', source)
        self.assertIn('"pending_resources": associations', source)
        card = (BASE / "www/energy-usage-utility-card.js").read_text()
        self.assertIn('response.pending_resources', card)
        self.assertIn('found.confirmed = Boolean(meter)', card)
        self.assertIn('select.disabled = busy || item.confirmed', card)


if __name__ == "__main__":
    unittest.main()
