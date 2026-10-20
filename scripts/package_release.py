#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build a reproducible, component-only ZIP for manual HA installation."""
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "energy_usage"


def make_archive(destination: Path) -> None:
    if not (COMPONENT / "manifest.json").is_file():
        raise SystemExit("Energy Usage integration manifest not found")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as output:
        for path in sorted(COMPONENT.rglob("*")):
            if not path.is_file():
                continue
            if "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            name = Path("custom_components/energy_usage") / (
                path.relative_to(COMPONENT)
            )
            info = zipfile.ZipInfo(name.as_posix(), (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100644 << 16)
            output.writestr(info, path.read_bytes())
    print(f"Created {destination}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    make_archive(parser.parse_args().output)
