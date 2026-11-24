# SPDX-License-Identifier: MIT
"""Portable documentation policy tests; Python standard library only."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "doc_policy", ROOT / "scripts/check_doc_policy.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DocumentationPolicyTests(unittest.TestCase):
    def check(self, name, contents):
        return MODULE.check_content(name, contents, release="0.1.5")

    def test_rejects_old_backend_requirement(self):
        self.assertTrue(self.check(
            "QUICKSTART.md",
            "Energy Ingest v0.1.10. Energy Ingest 0.1.9 is required"))

    def test_rejects_local_only_host_path(self):
        self.assertTrue(self.check(
            "QUICKSTART.md", "Energy Ingest v0.1.10. "
            "```bash\n$HOME/energy-ingest-prod/scripts/verify-prod.sh\n```"))

    def test_accepts_release_root_command(self):
        self.assertFalse(self.check(
            "QUICKSTART.md", "Energy Ingest v0.1.10. "
            "```bash\n./scripts/verify-prod.sh\n```"))

    def test_rejects_unknown_release_script(self):
        self.assertTrue(self.check(
            "QUICKSTART.md", "Energy Ingest v0.1.10.\n"
            "```bash\n./scripts/imaginary-helper.sh\n```"))

    def test_rejects_obsolete_catalog_message(self):
        self.assertTrue(self.check(
            "QUICKSTART.md", "Energy Ingest v0.1.10. "
            "Default HACS catalog inclusion is pending"))

    def test_rejects_private_host(self):
        self.assertTrue(self.check(
            "README.md", "Energy Ingest v0.1.10 on piha"))

    def test_rejects_internal_jargon_in_user_guides(self):
        self.assertTrue(self.check(
            "README.md", "Energy Ingest v0.1.10 acquisition source"))

    def test_rejects_missing_dashboard_or_reconfigure_guidance(self):
        self.assertTrue(self.check("INSTALLATION.md", "v0.1.10"))

    def test_rejects_unapproved_markdown_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / "docs/misc/example.md"
            p.parent.mkdir(parents=True)
            p.touch()
            self.assertTrue(MODULE.check_layout([p], root))

    def test_accepts_approved_markdown_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            files = []
            for rel in (
                "README.md", "docs/dev/AIUSAGE.md",
                "docs/testing/HA-TC-0001-energy-dashboard.md",
                "docs/adr/0003-example.md", "docs/UPGRADING.md",
                ".github/PULL_REQUEST_TEMPLATE.md",
            ):
                p = root / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.touch()
                files.append(p)
            self.assertEqual([], MODULE.check_layout(files, root))

    def test_rejects_stale_release_status(self):
        self.assertTrue(self.check(
            "docs/dev/ISSUE_TRACKING.md", "in-progress 0.1.5 release"))

    def test_rejects_external_release_output(self):
        self.assertTrue(self.check(
            "docs/dev/RELEASE_VERIFICATION.md", "/tmp/ha-energy-usage.zip"))


if __name__ == "__main__":
    unittest.main()
