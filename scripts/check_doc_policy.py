#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check current documentation placement, commands and configuration guidance.

Historical release notes, measured results and ADR decisions are preserved.
This checker uses only the Python standard library and never changes files.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOT_DOCS = {
    "README.md", "INSTALLATION.md", "QUICKSTART.md", "CHANGELOG.md",
    "CONTRIBUTING.md", "SECURITY.md", ".github/PULL_REQUEST_TEMPLATE.md",
}
DOC_DIRS = {"docs", "docs/adr", "docs/dev", "docs/testing"}
SKIP = {".git", ".venv", ".pytest_cache", "node_modules", "build",
        "dist", "__pycache__"}
PUBLIC = {
    "README.md", "INSTALLATION.md", "QUICKSTART.md",
    "docs/UPGRADING.md", "docs/TROUBLESHOOTING.md",
}
OUTDATED = (
    "upcoming v0.1.5", "v0.1.5 is being prepared",
    "in-progress 0.1.5 release", "energy ingest 0.1.9 is required",
    "default hacs catalog inclusion is pending",
    "default hacs catalog inclusion is a separate approval process",
)
# Actual executable scripts in the Energy Ingest v0.1.10 production release.
BACKEND_SCRIPTS = {
    "verify-prod.sh", "meter-prod.sh", "analyze-prod-data.sh",
}
PRIVATE = re.compile(
    r"(?:\$HOME|~)/energy-ingest-prod|/home/[^\s`]+|"
    r"/opt/homeassistant/config|/tmp/ha-energy-usage\.zip|"
    r"\b(?:piha(?:-w)?|sparta|pme991|hass_homeassistant)\b",
    re.I,
)
CODE = re.compile(r"^```([^\n]*)\n(.*?)^```\s*$", re.S | re.M)
SHELL_LOCAL = re.compile(
    r"(?:\$HOME|~)/energy-ingest-prod|/tmp/|/home/|"
    r"\bcd\s+~|\bcd\s+/opt/", re.I,
)
BACKEND_CALL = re.compile(r"(?:\./scripts/)([\w.-]+\.sh)")


def check_layout(paths: list[Path], root: Path) -> list[str]:
    issues = []
    for path in paths:
        rel = path.relative_to(root).as_posix()
        if rel in ROOT_DOCS:
            continue
        if str(Path(rel).parent) not in DOC_DIRS:
            issues.append(f"{rel}: Markdown outside approved directories")
    return issues


def check_content(rel: str, source: str, *, release: str) -> list[str]:
    """Return actionable violations without flagging historical version data."""
    issues = []
    lower = source.lower()
    if rel in PUBLIC:
        for phrase in OUTDATED:
            if phrase in lower:
                issues.append(f"{rel}: obsolete statement: {phrase}")
        if PRIVATE.search(source):
            issues.append(f"{rel}: private host or install directory")
        if f"v0.1.10" not in source:
            issues.append(f"{rel}: missing tested backend recommendation")
        if "acquisition source" in lower:
            issues.append(f"{rel}: internal jargon in public instructions")
        for match in CODE.finditer(source):
            lang, body = match.groups()
            if lang.strip().lower() not in {"bash", "sh", "shell"}:
                continue
            if SHELL_LOCAL.search(body):
                issues.append(f"{rel}: shell example uses local-only path")
            for script in BACKEND_CALL.findall(body):
                if script not in BACKEND_SCRIPTS:
                    issues.append(f"{rel}: unknown backend script {script}")
    if rel == "INSTALLATION.md":
        expected = (
            "./scripts/verify-prod.sh", "./scripts/meter-prod.sh list",
            "./scripts/analyze-prod-data.sh",
            "deploy/docker-compose/prod-secrets/ha_energy_dev_api_token",
            "custom_components/energy_usage/manifest.json",
            "HA_CONFIG_DIR", "Reconfigure", "Reauthenticate",
            "/energy-usage/energy-usage-explorer.js",
            "/energy-usage/energy-usage-utility-card.js",
            "type: custom:energy-usage-explorer",
            "type: custom:energy-usage-utility-card",
            "JavaScript module", "Tools → Statistics",
        )
        for item in expected:
            if item not in source:
                issues.append(f"{rel}: required setup detail missing: {item}")
        if "/energy_usage/" not in source:
            issues.append(f"{rel}: missing legacy URL migration note")
    if rel == "docs/UPGRADING.md":
        for item in ("Reconfigure", "Reauthenticate",
                     "/energy-usage/energy-usage-explorer.js"):
            if item not in source:
                issues.append(f"{rel}: upgrade guidance missing: {item}")
    if rel == "docs/TROUBLESHOOTING.md":
        if "Reconfigure" not in source:
            issues.append(f"{rel}: missing API reconnection advice")
    if rel == "docs/dev/ISSUE_TRACKING.md":
        if "in-progress 0.1.5" in lower:
            issues.append(f"{rel}: published release called in progress")
    if rel == "docs/dev/RELEASE_VERIFICATION.md":
        if "/tmp/ha-energy-usage.zip" in source:
            issues.append(f"{rel}: package output outside repository root")
        if "check_documentation.py" not in source:
            issues.append(f"{rel}: missing automated documentation gate")
    return issues


def check_tree(root: Path) -> list[str]:
    release = (root / "release/VERSION").read_text().strip()
    paths = sorted(p for p in root.rglob("*.md") if not (
        set(p.relative_to(root).parts) & SKIP))
    issues = check_layout(paths, root)
    for path in paths:
        rel = path.relative_to(root).as_posix()
        issues.extend(check_content(
            rel, path.read_text(encoding="utf-8"), release=release))
    return issues


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    issues = check_tree(args.root.resolve())
    if issues:
        for issue in issues:
            print(issue)
        raise SystemExit(f"Documentation policy: FAIL ({len(issues)} issues)")
    print("Documentation policy: PASS "
          "(directories, versions, installation, dashboard, commands)")


if __name__ == "__main__":
    main()
