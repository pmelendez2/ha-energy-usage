#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Verify and update explicitly tagged current documentation versions.

Historical release notes, ADR decisions and dated test evidence are not edited.
Use release/VERSION for Energy Usage and release/ENERGY_INGEST_VERSION for
recommended backend. Only spans with current-version markers are rewritten.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = re.compile(
    r"<!-- current-version:(ha-energy-usage|energy-ingest) -->"
    r"(v?)(\d+\.\d+\.\d+)"
    r"<!-- /current-version:\1 -->"
)
LOOSE = re.compile(r"<!-- current-version:(?:ha-energy-usage|energy-ingest) -->")
SEMVER = re.compile(r"\d+\.\d+\.\d+\Z")
SKIP = {".git", ".venv", ".pytest_cache", "node_modules", "build",
        "dist", "__pycache__"}
REQUIRED = {
    "README.md", "INSTALLATION.md", "QUICKSTART.md",
    "docs/UPGRADING.md", "docs/TROUBLESHOOTING.md",
}


def versions(root: Path) -> dict[str, str]:
    return {
        "ha-energy-usage": (root / "release/VERSION").read_text().strip(),
        "energy-ingest": (
            root / "release/ENERGY_INGEST_VERSION"
        ).read_text().strip(),
    }


def audit(root: Path, *, sync: bool = False) -> list[str]:
    expected = versions(root)
    issues: list[str] = []
    if not all(SEMVER.fullmatch(v) for v in expected.values()):
        return ["release/: invalid version metadata"]
    found: dict[str, set[str]] = {}
    files = sorted(p for p in root.rglob("*.md") if not (
        set(p.relative_to(root).parts) & SKIP))
    for path in files:
        rel = path.relative_to(root).as_posix()
        original = path.read_text(encoding="utf-8")
        # Release metadata is checked separately by the existing
        # release-version script and must stay plain text.
        for line in original.splitlines():
            if line.startswith("**Release:**") and (
                "<!-- current-version:" in line
            ):
                issues.append(
                    f"{rel}: current-version tag in Release metadata"
                )
        matches = list(MARKER.finditer(original))
        if len(matches) != len(LOOSE.findall(original)):
            issues.append(f"{rel}: malformed current-version marker")
        found[rel] = {m.group(1) for m in matches}
        for m in matches:
            if not sync and m.group(3) != expected[m.group(1)]:
                issues.append(f"{rel}: {m.group(1)} is {m.group(3)}; "
                              f"expected {expected[m.group(1)]}")
        if sync and matches:
            updated = MARKER.sub(
                lambda m: (f"<!-- current-version:{m.group(1)} -->"
                           f"{m.group(2)}{expected[m.group(1)]}"
                           f"<!-- /current-version:{m.group(1)} -->"),
                original,
            )
            if updated != original:
                path.write_text(updated, encoding="utf-8")
                print(f"SYNC {rel}")
    for rel in sorted(REQUIRED):
        if found.get(rel, set()) != set(expected):
            issues.append(f"{rel}: expected both current-version markers")
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--sync", action="store_true")
    group.add_argument("--set-energy-ingest", metavar="VERSION")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.set_energy_ingest is not None:
        if not SEMVER.fullmatch(args.set_energy_ingest):
            parser.error("expected a version such as 0.1.10")
        (root / "release/ENERGY_INGEST_VERSION").write_text(
            args.set_energy_ingest + "\n", encoding="utf-8")
    errors = audit(root, sync=args.sync or args.set_energy_ingest is not None)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(f"Version tags: FAIL ({len(errors)} errors)")
    print("Version tags: PASS (separate integration/backend version metadata)")


if __name__ == "__main__":
    main()
