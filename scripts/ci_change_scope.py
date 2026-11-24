#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Fail-closed classification of changes for GitHub Actions.

Docs-only and workflow-only edits skip unrelated runtime tests. Any source,
release, dependency, test, script, unknown or deleted non-doc path runs full CI.
"""
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path


def classify(paths: list[str]) -> str:
    if not paths:
        return "full"
    scopes: set[str] = set()
    for path in paths:
        if path.endswith(".md"):
            scopes.add("docs")
        elif (path.startswith(".github/workflows/") and
              path.endswith((".yml", ".yaml")) or
              path == ".github/dependabot.yml"):
            scopes.add("workflow")
        else:
            return "full"
    return "workflow" if "workflow" in scopes else "docs"


def changed_paths(base: str, head: str) -> list[str]:
    # -z handles spaces, tabs, and rename/copy paths safely.
    result = subprocess.run(
        ["git", "diff", "--name-status", "-z", "--find-renames",
         base, head],
        check=True, capture_output=True,
    )
    fields = result.stdout.decode("utf-8").split("\0")
    if fields[-1] != "":
        raise ValueError("unexpected un-terminated git diff output")
    paths: list[str] = []
    pos = 0
    while pos < len(fields) - 1:
        status = fields[pos]
        pos += 1
        count = 2 if status.startswith(("R", "C")) else 1
        if pos + count > len(fields) - 1:
            raise ValueError("incomplete git diff record")
        paths.extend(fields[pos:pos + count])
        pos += count
    return paths


def resolve_base(event: str, base: str, head: str) -> str | None:
    if event == "workflow_dispatch":
        return None
    if not base or base == "0" * 40:
        return None
    subprocess.run(["git", "cat-file", "-e", f"{base}^{{commit}}"],
                   check=True, capture_output=True)
    subprocess.run(["git", "cat-file", "-e", f"{head}^{{commit}}"],
                   check=True, capture_output=True)
    if event == "pull_request":
        result = subprocess.run(["git", "merge-base", base, head],
                                check=True, capture_output=True, text=True)
        return result.stdout.strip()
    if event == "push":
        return base
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True)
    parser.add_argument("--base", default="")
    parser.add_argument("--head", default="HEAD")
    args = parser.parse_args()
    scope = "full"
    comparison_base = ""
    try:
        comparison_base = resolve_base(args.event, args.base, args.head) or ""
        if comparison_base:
            scope = classify(changed_paths(comparison_base, args.head))
    except (OSError, subprocess.CalledProcessError, ValueError, UnicodeError) as exc:
        # Missing history or malformed change data must never skip checks.
        print(f"Change classification unavailable; running full CI: {exc}")
        comparison_base = ""
        scope = "full"

    # Main always gets full validation, including after merging a docs PR.
    if os.environ.get("GITHUB_REF") == "refs/heads/main":
        scope = "full"

    print(f"CI scope: {scope}")
    if comparison_base:
        print(f"Comparing {comparison_base}..{args.head}")
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with Path(output).open("a", encoding="utf-8") as stream:
            stream.write(f"scope={scope}\n")
            stream.write(f"base={comparison_base}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
