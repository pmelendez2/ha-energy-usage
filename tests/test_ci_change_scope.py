# SPDX-License-Identifier: MIT
"""Change classification fail-closed regression tests."""
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "scripts/ci_change_scope.py"
SPEC = importlib.util.spec_from_file_location("ci_change_scope", MODULE)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class ChangeScopeTest(unittest.TestCase):
    def test_docs(self):
        self.assertEqual(mod.classify(["README.md", "docs/SETUP.md"]), "docs")

    def test_workflow(self):
        self.assertEqual(mod.classify([".github/workflows/ci.yml"]), "workflow")

    def test_mixed_docs_workflow(self):
        self.assertEqual(mod.classify(["README.md", ".github/dependabot.yml"]),
                         "workflow")

    def test_code_and_tests_are_full(self):
        for path in ("custom_components/energy_usage/__init__.py",
                     "tests/test_history.py", "scripts/check_documentation.py",
                     "release/VERSION", "Dockerfile", ".github/unknown.yml",
                     "requirements.txt", "README.txt"):
            with self.subTest(path=path):
                self.assertEqual(mod.classify([path]), "full")

    def test_unknown_or_empty_are_full(self):
        self.assertEqual(mod.classify([]), "full")
        self.assertEqual(mod.classify(["docs/README.md", "unknown.bin"]),
                         "full")

    def test_rename_including_non_docs_is_full(self):
        self.assertEqual(mod.classify(["docs/a.md", "scripts/a.py"]),
                         "full")

    def test_name_status_parser_renames(self):
        import subprocess
        from unittest.mock import patch
        outcome = subprocess.CompletedProcess([], 0,
            stdout=b"R100\0docs/old.md\0docs/new.md\0D\0script.sh\0")
        with patch.object(mod.subprocess, "run", return_value=outcome):
            self.assertEqual(mod.changed_paths("a", "b"),
                             ["docs/old.md", "docs/new.md", "script.sh"])

    def test_bad_diff_fails_closed(self):
        import subprocess
        from unittest.mock import patch
        outcome = subprocess.CompletedProcess([], 0, stdout=b"M\0a.md")
        with patch.object(mod.subprocess, "run", return_value=outcome):
            with self.assertRaises(ValueError):
                mod.changed_paths("a", "b")


if __name__ == "__main__":
    unittest.main()
