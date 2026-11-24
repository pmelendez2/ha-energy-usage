# SPDX-License-Identifier: MIT
"""Release issue-link policy regression tests."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check_issue_links.py"
spec = importlib.util.spec_from_file_location("issue_links", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
BASE = "https://github.com/pmelendez2/ha-energy-usage/issues/"


def doc(body, version="0.1.6"):
    return (f"# Changelog\n\n## Unreleased — v{version}\n\n"
            f"### Issues resolved\n\n{body}\n\n### Verification\n\nOK\n")


class IssueLinkTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(module.validate_text(doc(
            f"- [#14 — Fix]({BASE}14): Corrected behavior."), "0.1.6"), [])

    def test_none(self):
        self.assertEqual(module.validate_text(doc("None"), "0.1.6"), [])

    def test_missing_section(self):
        self.assertTrue(module.validate_text(
            "# Changelog\n## Unreleased — v0.1.6\n", "0.1.6"))

    def test_wrong_target(self):
        self.assertTrue(module.validate_text(doc(
            f"- [#14 — Fix]({BASE}15): Corrected."), "0.1.6"))

    def test_duplicates(self):
        link = f"- [#14 — Fix]({BASE}14): Corrected."
        self.assertTrue(module.validate_text(doc(link + "\n" + link), "0.1.6"))

    def test_bare_number(self):
        self.assertTrue(module.validate_text(doc("Fixed #14"), "0.1.6"))

    def test_wrong_repo(self):
        self.assertTrue(module.validate_text(doc(
            "- [#14](https://github.com/other/repo/issues/14)"), "0.1.6"))

    def test_historical_baseline_unchanged(self):
        self.assertEqual(module.validate_text("# Changelog\n", "0.1.5"), [])

    def test_wrong_version(self):
        self.assertTrue(module.validate_text(doc("None", "0.1.7"), "0.1.6"))


if __name__ == "__main__":
    unittest.main()
