#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Synchronize current release metadata without rewriting history."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "release/VERSION"
MANIFEST = ROOT / "custom_components/energy_usage/manifest.json"
PROJECT = ROOT / "pyproject.toml"
SKIP = {".git", ".venv", ".pytest_cache", "node_modules",
        "build", "dist"}
RELEASE_LINE = re.compile(r"(?m)^(\*\*Release:\*\* )([^\r\n]+)$")
PROJECT_VERSION = re.compile(r'(?m)^(version\s*=\s*")([^"]+)(")$')


def documents(root: Path):
    return sorted(p for p in root.rglob("*.md")
                  if not (set(p.relative_to(root).parts) & SKIP))


def synchronize(root: Path, version: str, *, check: bool) -> list[str]:
    """Return discrepancies; modify only current release metadata if requested."""
    errors = []
    for path in documents(root):
        source = path.read_text(encoding="utf-8")
        matches = list(RELEASE_LINE.finditer(source))
        if len(matches) != 1:
            errors.append(f"{path.relative_to(root)}: expected one Release field")
            continue
        if matches[0].group(2).strip() == version:
            continue
        errors.append(f"{path.relative_to(root)}: release mismatch")
        if not check:
            updated = RELEASE_LINE.sub(lambda m: m.group(1) + version,
                                       source, count=1)
            path.write_text(updated, encoding="utf-8")

    manifest = root / "custom_components/energy_usage/manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("version") != version:
        errors.append("manifest.json: version mismatch")
        if not check:
            data["version"] = version
            # Preserve formatting and key ordering of the existing manifest.
            source = manifest.read_text(encoding="utf-8")
            source, n = re.subn(
                r'("version"\s*:\s*")[^"]+(" )',
                lambda m: m.group(1) + version + m.group(2), source)
            if not n:
                source, n = re.subn(
                    r'("version"\s*:\s*")[^"]+("(?=\s*[,}]))',
                    lambda m: m.group(1) + version + m.group(2), source)
            if n != 1:
                raise ValueError("Unexpected manifest version format")
            manifest.write_text(source, encoding="utf-8")

    project = root / "pyproject.toml"
    source = project.read_text(encoding="utf-8")
    matches = list(PROJECT_VERSION.finditer(source))
    if len(matches) != 1:
        errors.append("pyproject.toml: expected one project version")
    elif matches[0].group(2) != version:
        errors.append("pyproject.toml: version mismatch")
        if not check:
            project.write_text(PROJECT_VERSION.sub(
                lambda m: m.group(1) + version + m.group(3),
                source, count=1), encoding="utf-8")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--set", dest="new_version")
    args = parser.parse_args()
    if args.check and args.new_version:
        parser.error("--check and --set are mutually exclusive")
    version = (args.new_version or VERSION_FILE.read_text().strip())
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        parser.error("Expected semantic version such as 0.1.2")
    if args.new_version:
        VERSION_FILE.write_text(version + "\n", encoding="utf-8")
    errors = synchronize(ROOT, version, check=args.check)
    if args.check and errors:
        print("\n".join(errors))
        raise SystemExit(f"Release metadata: FAIL ({len(errors)} issues)")
    print(f"Release metadata: PASS ({version}, {len(errors)} updated)")


if __name__ == "__main__":
    main()
