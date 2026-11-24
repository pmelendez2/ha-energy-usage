#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Validate change-aware workflow syntax and protection-critical contracts."""
from __future__ import annotations

from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github/workflows"


def check() -> list[str]:
    errors: list[str] = []
    for file in sorted(WORKFLOWS.glob("*.yml")):
        try:
            data = yaml.safe_load(file.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("jobs"), dict):
                errors.append(f"{file.name}: missing jobs mapping")
        except yaml.YAMLError as exc:
            errors.append(f"{file.name}: invalid YAML: {exc}")
    ci = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    # Keep the always-present branch-protection context and detection steps.
    for token in ("  isolated:", "    name: isolated", "id: scope",
                  "scripts/ci_change_scope.py",
                  "scripts/verify-release.sh",
                  "VERIFY_RELEASE_CHANGE_BASE"):
        if token not in ci:
            errors.append(f"ci.yml: missing required gate: {token}")
    for name in ("compatibility.yml", "hacs-validation.yml"):
        s = (WORKFLOWS / name).read_text(encoding="utf-8")
        for token in ("id: scope", "scripts/ci_change_scope.py",
                      "needs.changes.outputs.scope == 'full'"):
            if token not in s:
                errors.append(f"{name}: missing change-aware gate: {token}")
    return errors


if __name__ == "__main__":
    problems = check()
    if problems:
        print("\n".join(problems))
        raise SystemExit(1)
    print("CI workflow contracts: PASS")
