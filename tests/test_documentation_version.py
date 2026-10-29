# SPDX-License-Identifier: MIT
"""Regression tests for release metadata synchronization."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/update_documentation_version.py"
spec = importlib.util.spec_from_file_location("doc_version", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DocumentationVersionTests(unittest.TestCase):
    def test_release_version_matches_manifest_and_project(self):
        version = (ROOT / "release/VERSION").read_text().strip()
        self.assertEqual(json.loads(module.MANIFEST.read_text())["version"],
                         version)
        self.assertEqual(module.synchronize(ROOT, version, check=True), [])

    def test_only_current_release_metadata_changes(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "custom_components/energy_usage").mkdir(parents=True)
            (root / "docs").mkdir()
            (root / "docs/history.md").write_text(
                "<!-- SPDX-License-Identifier: MIT -->\n"
                "# History\n\n**Release:** 0.1.1\n\n"
                "Previously published 0.1.0 and 0.1.1.\n")
            (root / "custom_components/energy_usage/manifest.json").write_text(
                '{"version": "0.1.1"}\n')
            (root / "pyproject.toml").write_text(
                '[project]\nversion = "0.1.1"\n')
            self.assertEqual(len(module.synchronize(root, "0.1.2", check=True)), 3)
            module.synchronize(root, "0.1.2", check=False)
            self.assertEqual(module.synchronize(root, "0.1.2", check=True), [])
            content = (root / "docs/history.md").read_text()
            self.assertIn("**Release:** 0.1.2", content)
            self.assertIn("Previously published 0.1.0 and 0.1.1", content)
            self.assertEqual(module.synchronize(root, "0.1.2", check=False), [])


if __name__ == "__main__":
    unittest.main()
