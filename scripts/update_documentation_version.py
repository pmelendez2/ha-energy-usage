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
VERSION_PATTERN = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
MANIFEST_VERSION = re.compile(
    r'("version"\s*:\s*")[^"]+("(?=\s*[,}]))'
)


def documents(root: Path):
    return sorted(p for p in root.rglob("*.md")
                  if not (set(p.relative_to(root).parts) & SKIP))


def plan(root: Path, version: str) -> tuple[dict[Path, str], list[str]]:
    """Compute every replacement before permitting any file writes."""
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError("Expected semantic version such as 0.1.2")
    updates: dict[Path, str] = {}
    errors: list[str] = []
    for path in documents(root):
        source = path.read_text(encoding="utf-8")
        matches = list(RELEASE_LINE.finditer(source))
        if len(matches) != 1:
            errors.append(f"{path.relative_to(root)}: expected one Release field")
            continue
        if matches[0].group(2).strip() != version:
            errors.append(f"{path.relative_to(root)}: release mismatch")
            updates[path] = RELEASE_LINE.sub(
                lambda m: m.group(1) + version, source, count=1
            )

    manifest = root / "custom_components/energy_usage/manifest.json"
    source = manifest.read_text(encoding="utf-8")
    data = json.loads(source)
    matches = list(MANIFEST_VERSION.finditer(source))
    if len(matches) != 1:
        errors.append("manifest.json: expected one version field")
    elif data.get("version") != version:
        errors.append("manifest.json: version mismatch")
        updates[manifest] = MANIFEST_VERSION.sub(
            lambda m: m.group(1) + version + m.group(2),
            source, count=1
        )

    project = root / "pyproject.toml"
    source = project.read_text(encoding="utf-8")
    matches = list(PROJECT_VERSION.finditer(source))
    if len(matches) != 1:
        errors.append("pyproject.toml: expected one project version")
    elif matches[0].group(2) != version:
        errors.append("pyproject.toml: version mismatch")
        updates[project] = PROJECT_VERSION.sub(
            lambda m: m.group(1) + version + m.group(3),
            source, count=1
        )
    return updates, errors


def synchronize(root: Path, version: str, *, check: bool) -> list[str]:
    """Check or apply metadata; reject malformed files before writing."""
    updates, errors = plan(root, version)
    if not check:
        if len(errors) != len(updates):
            raise ValueError("Invalid metadata; no files were modified: "
                             + "; ".join(errors))
        for path, content in updates.items():
            path.write_text(content, encoding="utf-8")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--set", dest="new_version")
    args = parser.parse_args()
    if args.check and args.new_version:
        parser.error("--check and --set are mutually exclusive")
    version = args.new_version or VERSION_FILE.read_text().strip()
    if not VERSION_PATTERN.fullmatch(version):
        parser.error("Expected semantic version such as 0.1.2")
    updates, errors = plan(ROOT, version)
    if args.check:
        if errors:
            print("\n".join(errors))
            raise SystemExit(
                f"Release metadata: FAIL ({len(errors)} issues)"
            )
    else:
        if len(errors) != len(updates):
            raise SystemExit("Release metadata: FAIL (invalid file format; "
                             "nothing changed): " + "; ".join(errors))
        # All metadata is validated before changing the canonical version.
        for path, content in updates.items():
            path.write_text(content, encoding="utf-8")
        if args.new_version:
            VERSION_FILE.write_text(version + "\n", encoding="utf-8")
    print(f"Release metadata: PASS ({version}, "
          f"{0 if args.check else len(updates)} updated)")


if __name__ == "__main__":
    main()
