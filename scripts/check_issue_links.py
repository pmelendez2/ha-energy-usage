#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Validate issue references in the current CHANGELOG release entry."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ISSUE_URL = "https://github.com/pmelendez2/ha-energy-usage/issues/"
LINK = re.compile(
    r"\[#([1-9][0-9]*)[^\]\n]*\]\("
    + re.escape(ISSUE_URL) + r"([1-9][0-9]*)\)"
)
BARE = re.compile(r"(?<![\w/])#[1-9][0-9]*\b")


def validate_text(content: str, version: str) -> list[str]:
    """Require issue evidence for releases prepared after policy adoption."""
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        return ["Invalid release version"]
    # v0.1.5 is already under preparation: do not rewrite historical claims.
    if tuple(map(int, version.split("."))) <= (0, 1, 5):
        return []
    entries = list(re.finditer(r"(?m)^## (.+)$", content))
    selected = None
    for index, entry in enumerate(entries):
        heading = entry.group(1)
        if re.search(rf"(?<!\d){re.escape(version)}(?!\d)", heading):
            end = entries[index + 1].start() if index + 1 < len(entries) else len(content)
            selected = content[entry.end():end]
            break
    if selected is None:
        return [f"CHANGELOG.md: missing release section for {version}"]
    part = re.search(
        r"(?ms)^### Issues resolved\s*\n(.*?)(?=^### |\Z)", selected
    )
    if part is None:
        return ["CHANGELOG.md: missing Issues resolved subsection"]
    body = part.group(1).strip()
    if body == "None":
        return []
    if not body:
        return ["CHANGELOG.md: Issues resolved must contain links or None"]
    links = LINK.findall(body)
    if not links:
        return ["CHANGELOG.md: Issues resolved needs direct Markdown issue links or None"]
    if any(label != target for label, target in links):
        return ["CHANGELOG.md: issue label and URL number differ"]
    if len(links) != len({target for _, target in links}):
        return ["CHANGELOG.md: duplicate resolved issue links"]
    remaining = LINK.sub("", body)
    if BARE.search(remaining):
        return ["CHANGELOG.md: bare issue numbers; use direct links"]
    if re.search(r"\bNone\b", remaining):
        return ["CHANGELOG.md: None conflicts with listed issues"]
    return []


def validate(root: Path = ROOT) -> list[str]:
    version = (root / "release/VERSION").read_text(encoding="utf-8").strip()
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    return validate_text(changelog, version)


if __name__ == "__main__":
    errors = validate()
    if errors:
        raise SystemExit("\n".join(errors))
    print("Issue-linked changelog validation: PASS")
