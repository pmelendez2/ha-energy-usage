# SPDX-License-Identifier: MIT
"""Checks for current documentation version markers and historical safety."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from manage_doc_versions import REQUIRED, audit


class TestDocVersions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "release").mkdir()
        (self.root / "release/VERSION").write_text("0.1.5\n")
        (self.root / "release/ENERGY_INGEST_VERSION").write_text(
            "0.1.10\n")
        self.docs = {}
        for name in REQUIRED:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "Current <!-- current-version:ha-energy-usage -->"
                "v0.1.5<!-- /current-version:ha-energy-usage -->\n"
                "Backend <!-- current-version:energy-ingest -->"
                "v0.1.10<!-- /current-version:energy-ingest -->\n"
                "Historical v0.1.9 was tested.\n",
                encoding="utf-8",
            )
            self.docs[name] = path

    def tearDown(self):
        self.temp.cleanup()

    def test_current_is_valid(self):
        self.assertEqual(audit(self.root), [])

    def test_backend_version_change_requires_sync(self):
        (self.root / "release/ENERGY_INGEST_VERSION").write_text("0.1.11\n")
        self.assertTrue(audit(self.root))
        self.assertEqual(audit(self.root, sync=True), [])
        self.assertEqual(audit(self.root), [])
        for path in self.docs.values():
            s = path.read_text()
            self.assertIn("v0.1.11", s)
            self.assertIn("Historical v0.1.9 was tested.", s)

    def test_integration_version_change_requires_sync(self):
        (self.root / "release/VERSION").write_text("0.1.6\n")
        self.assertTrue(audit(self.root))
        self.assertEqual(audit(self.root, sync=True), [])
        self.assertEqual(audit(self.root), [])
        for path in self.docs.values():
            self.assertIn("v0.1.6", path.read_text())

    def test_release_metadata_must_not_be_tagged(self):
        p = self.docs["docs/UPGRADING.md"]
        p.write_text("**Release:** " + p.read_text())
        self.assertTrue(any(
            "tag in Release metadata" in issue
            for issue in audit(self.root)
        ))

    def test_missing_marker_fails(self):
        self.docs["README.md"].write_text("No version marker\n")
        self.assertTrue(any("README.md" in s for s in audit(self.root)))

    def test_malformed_marker_fails(self):
        p = self.docs["README.md"]
        p.write_text(p.read_text().replace(
            "<!-- /current-version:energy-ingest -->", ""))
        self.assertTrue(any("malformed" in s for s in audit(self.root)))


if __name__ == "__main__":
    unittest.main()
