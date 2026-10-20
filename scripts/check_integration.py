#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check release-critical manifest, translations, and branding."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "energy_usage"


def check() -> None:
    manifest = json.loads((COMPONENT / "manifest.json").read_text())
    hacs = json.loads((ROOT / "hacs.json").read_text())
    assert manifest["domain"] == "energy_usage"
    assert manifest["config_flow"] is True
    assert manifest["version"]
    assert isinstance(hacs, dict)
    strings = json.loads((COMPONENT / "strings.json").read_text())
    translation = json.loads(
        (COMPONENT / "translations" / "en.json").read_text()
    )
    assert strings == translation, "English translation and strings differ"
    for name in ("icon.png", "icon@2x.png"):
        path = COMPONENT / "brand" / name
        assert path.is_file(), f"Missing brand asset: {name}"
        assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    print("Integration manifest, JSON and branding: PASS")


if __name__ == "__main__":
    check()
