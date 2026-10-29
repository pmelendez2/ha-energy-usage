# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Contract checks for read-only preflight action and guarded wiring."""

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "custom_components/energy_usage/statistics_sync_preflight_service.py"
PATCH = ROOT / "scripts/apply-sync-preflight.py"


class PreflightActionTests(unittest.TestCase):
    def test_service_is_explicit_and_read_only(self):
        content = SERVICE.read_text()
        tree = ast.parse(content)
        names = {node.name for node in tree.body
                 if isinstance(node, ast.AsyncFunctionDef)}
        self.assertIn("async_register_preflight_service", names)
        self.assertIn("preflight_one", names)
        self.assertIn("await assess_meter(", content)
        self.assertNotIn("async_add_external_statistics", content)
        self.assertNotIn("sync_owned_statistics", content)

    def test_lifecycle_patcher_has_safe_anchors(self):
        content = PATCH.read_text()
        self.assertIn("source.count(anchor) != 1", content)
        self.assertIn("SYNC_SERVICE", content)
        self.assertIn("PREFLIGHT_SERVICE", content)

    def test_report_contains_counts_and_no_write_notice(self):
        source = SERVICE.read_text()
        for item in ("existing=%d", "canonical=%d", "added=%d",
                     "corrected=%d", "unchanged=%d", "NO RECORDER WRITES"):
            self.assertIn(item, source)


if __name__ == "__main__":
    unittest.main()
