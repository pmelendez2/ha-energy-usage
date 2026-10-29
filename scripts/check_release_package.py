#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Validate a component-only release ZIP without unpacking it."""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "custom_components/energy_usage/"
REQUIRED = {
    PREFIX + "manifest.json",
    PREFIX + "__init__.py",
    PREFIX + "services.yaml",
    PREFIX + "history_import_service.py",
    PREFIX + "statistics_import.py",
    PREFIX + "www/energy-usage-explorer.js",
    PREFIX + "strings.json",
    PREFIX + "translations/en.json",
    PREFIX + "brand/icon.png",
    PREFIX + "brand/icon@2x.png",
}


def check(path: str, expected_version: str | None = None) -> None:
    if expected_version is None:
        expected_version = (ROOT / "release/VERSION").read_text(
            encoding="utf-8"
        ).strip()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", expected_version):
        raise ValueError("Invalid canonical release version")

    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)), "Duplicate members"
        assert REQUIRED.issubset(names), "Missing required integration members"
        for name in names:
            parts = PurePosixPath(name)
            assert not parts.is_absolute() and ".." not in parts.parts
            assert name.startswith(PREFIX), f"Unexpected ZIP member: {name}"
            assert "__pycache__" not in name and not name.endswith(".pyc")
        manifest = json.loads(archive.read(PREFIX + "manifest.json"))
        assert manifest["domain"] == "energy_usage"
        assert manifest["version"] == expected_version, (
            "Release ZIP version mismatch: "
            f"expected {expected_version}, found {manifest['version']}"
        )
    print(f"Release ZIP: PASS ({len(names)} files, "
          f"version {expected_version})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive")
    check(parser.parse_args().archive)
