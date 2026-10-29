# SPDX-License-Identifier: MIT
"""Regression coverage for release metadata and ZIP consistency."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


updater = load("release_updater", ROOT / "scripts/update_documentation_version.py")
checker = load("release_checker", ROOT / "scripts/check_release_package.py")


class ReleaseConsistencyTests(unittest.TestCase):
    def make_root(self, root, malformed=False):
        (root / "docs").mkdir()
        (root / "custom_components/energy_usage").mkdir(parents=True)
        (root / "release").mkdir()
        (root / "release/VERSION").write_text("0.1.1\n")
        (root / "docs/history.md").write_text(
            "# History\n\n**Release:** 0.1.1\n\n"
            "Published 0.1.0 remains historical.\n"
        )
        (root / "custom_components/energy_usage/manifest.json").write_text(
            '{"domain": "energy_usage", "version": "0.1.1"}\n'
        )
        (root / "pyproject.toml").write_text(
            '[project]\nname = "energy-usage"\n' +
            ('invalid = "0.1.1"\n' if malformed else
             'version = "0.1.1"\n')
        )

    def test_planning_does_not_modify_files(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_root(root)
            updates, errors = updater.plan(root, "0.1.2")
            self.assertEqual(len(updates), 3)
            self.assertEqual(len(errors), 3)
            self.assertEqual((root / "release/VERSION").read_text(),
                             "0.1.1\n")
            self.assertIn("Published 0.1.0",
                          (root / "docs/history.md").read_text())

    def test_malformed_metadata_blocks_all_writes(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_root(root, malformed=True)
            with self.assertRaises(ValueError):
                updater.synchronize(root, "0.1.2", check=False)
            self.assertIn("**Release:** 0.1.1",
                          (root / "docs/history.md").read_text())
            self.assertEqual((root / "release/VERSION").read_text(),
                             "0.1.1\n")

    def test_archive_rejects_version_mismatch(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "release.zip"
            with zipfile.ZipFile(path, "w") as archive:
                for name in checker.REQUIRED:
                    payload = b"placeholder"
                    if name == checker.PREFIX + "manifest.json":
                        payload = json.dumps({
                            "domain": "energy_usage", "version": "0.1.1"
                        }).encode()
                    archive.writestr(name, payload)
            with self.assertRaisesRegex(AssertionError, "version mismatch"):
                checker.check(str(path), "0.1.2")
            checker.check(str(path), "0.1.1")


if __name__ == "__main__":
    unittest.main()
