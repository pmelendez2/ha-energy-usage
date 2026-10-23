#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Validate the exact release ZIP without unpacking it."""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import PurePosixPath

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


def check(path: str) -> None:
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
        assert manifest["version"]
    print(f"Release ZIP: PASS ({len(names)} files)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive")
    check(parser.parse_args().archive)
