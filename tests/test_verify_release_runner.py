# SPDX-License-Identifier: MIT
"""Contract tests for the canonical release verification shell runner."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/verify-release.sh"


class VerifyReleaseRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name) / "repo"
        scripts = self.root / "scripts"
        scripts.mkdir(parents=True)
        shutil.copy2(RUNNER, scripts / "verify-release.sh")
        bins = self.root / "bin"
        bins.mkdir()
        self.calls = self.root / "calls"
        # Command shims exercise orchestration without recursively running
        # the entire real suite each time these tests execute.
        for name in ("python3", "node", "git"):
            shim = bins / name
            shim.write_text(
                "#!/bin/sh\n"
                'printf "%s %s\\n" "$(basename "$0")" "$*" '
                '>> "$VERIFY_TEST_CALLS"\n'
                'if [ "${VERIFY_TEST_FAIL:-}" = "$(basename "$0")" ]; '
                'then exit 17; fi\n'
                'if [ "$(basename "$0")" = git ] && '
                '[ "$1" = rev-parse ]; then exit 1; fi\n',
                encoding="utf-8",
            )
            shim.chmod(0o755)
        self.env = dict(os.environ)
        self.env["PATH"] = f"{bins}:{os.environ.get('PATH', '')}"
        self.env["VERIFY_TEST_CALLS"] = str(self.calls)
        self.env.pop("VERIFY_RELEASE_CHANGE_BASE", None)

    def invoke(self, scope: str = "full", *, cwd: Path | None = None,
               env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(self.root / "scripts/verify-release.sh"),
             "--scope", scope],
            cwd=cwd or self.root, env=env or self.env,
            capture_output=True, text=True, check=False,
        )

    def test_full_runs_all_checks_and_package(self) -> None:
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Release verification: PASS (full scope)", result.stdout)
        calls = self.calls.read_text(encoding="utf-8")
        for token in ("manage_doc_versions.py --check", "-m unittest",
                      "node --check", "package_release.py",
                      "check_release_package.py", "git diff --check"):
            self.assertIn(token, calls)

    def test_docs_scope_avoids_runtime_tests(self) -> None:
        result = self.invoke("docs")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.calls.read_text(encoding="utf-8")
        self.assertIn("check_documentation.py", calls)
        self.assertNotIn("package_release.py", calls)
        self.assertNotIn("-m unittest", calls)

    def test_failure_propagates_without_false_pass(self) -> None:
        env = dict(self.env)
        env["VERIFY_TEST_FAIL"] = "node"
        result = self.invoke(env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Explorer JavaScript syntax failed", result.stderr)
        self.assertNotIn("Release verification: PASS", result.stdout)

    def test_root_independent_and_repeatable(self) -> None:
        for _ in range(2):
            result = self.invoke("workflow", cwd=Path(self.workspace.name))
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls.read_text().count("check_ci_workflows.py"), 2)

    def test_invalid_scope_is_rejected(self) -> None:
        result = self.invoke("unknown")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported verification scope", result.stderr)

    def test_ci_base_is_used_for_whitespace_check(self) -> None:
        env = dict(self.env)
        env["VERIFY_RELEASE_CHANGE_BASE"] = "base123"
        env["GITHUB_SHA"] = "head456"
        result = self.invoke("docs", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("git diff --check base123 head456",
                      self.calls.read_text())


if __name__ == "__main__":
    unittest.main()
