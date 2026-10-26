#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Create a review snapshot from the current Git working tree.
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
if [[ "$(pwd -P)" != "$repo_root" ]]; then
    printf 'Run from repository root: %s\n' "$repo_root" >&2
    exit 1
fi

python3 - "$repo_root" <<'PY'
# SPDX-License-Identifier: MIT
"""Build a bounded, reviewed-source-only working-tree archive."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import zipfile

root = Path(sys.argv[1])
revision = subprocess.check_output(
    ["git", "rev-parse", "--short=12", "HEAD"],
    cwd=root, text=True,
).strip()
now = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
output = root / f"ha_energy_usage_review_{now}.zip"

# Explicit source/documentation allowlist, not a general backup.
allowed_roots = {
    "custom_components", "tests", "docs", "scripts", ".github",
}
allowed_top = {
    "README.md", "INSTALLATION.md", "LICENSE",
    "CHANGELOG.md", "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md", "SECURITY.md", "pyproject.toml",
    "pytest.ini", "requirements.txt", "requirements_test.txt",
    "requirements_dev.txt", "hacs.json", ".gitignore",
    ".pre-commit-config.yaml", "ruff.toml", "mypy.ini",
}
allowed_suffixes = {
    ".py", ".js", ".cjs", ".mjs",
    ".md", ".json", ".toml", ".yaml", ".yml",
    ".sh", ".txt", ".ini", ".cfg", ".po", ".pot",
}
blocked_parts = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".ruff_cache", ".mypy_cache", "node_modules", "secrets",
    "private", "data", "backups", "downloads", ".storage",
    "coverage", "dist", "build", "logs", "fixtures-private",
}
blocked_names = {
    ".env", "secrets.yaml", "configuration.yaml", "auth", "auth_provider.homeassistant",
    "known_devices.yaml", "known_devices", "home-assistant_v2.db",
}

def included(path: Path) -> bool:
    parts = path.parts
    if not parts or any(p in blocked_parts for p in parts):
        return False
    if any(p.startswith(".env") or p.endswith((".key", ".pem", ".p12", ".pfx"))
           for p in parts):
        return False
    if (
        len(parts) == 4
        and parts[:3] == (
            "custom_components", "energy_usage", "brand"
        )
        and path.name in {"icon.png", "icon@2x.png"}
    ):
        return True
    if path.name in blocked_names:
        return False
    if str(path) in allowed_top:
        return True
    if path.suffix.lower() not in allowed_suffixes:
        return False
    return parts[0] in allowed_roots

raw = subprocess.check_output(
    ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
    cwd=root,
)
paths = sorted(set(Path(item.decode("utf-8")) for item in raw.split(b"\0") if item))
added = []
skipped = 0
with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
    for relative in paths:
        full = root / relative
        if not included(relative) or not full.is_file() or full.is_symlink():
            skipped += 1
            continue
        if full.stat().st_size > 2_000_000:
            skipped += 1
            continue
        archive.write(full, arcname=relative.as_posix())
        added.append(relative.as_posix())

print(f"Archive: {output}")
print(f"Git revision: {revision}")
print(f"Included source/documentation files: {len(added)}")
print(f"Excluded or skipped files: {skipped}")
print("Review archive contents before uploading; source may contain secrets.")
if not added:
    output.unlink(missing_ok=True)
    raise SystemExit("No eligible files found")
with zipfile.ZipFile(output) as archive:
    bad = archive.testzip()
    if bad:
        raise SystemExit(f"Archive integrity failure: {bad}")
print("ZIP integrity: OK")
PY
