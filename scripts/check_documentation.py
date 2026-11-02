#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check documentation metadata, local links, and release consistency."""
from __future__ import annotations

import json
from update_documentation_version import synchronize
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'custom_components/energy_usage/manifest.json'
VERSION = (ROOT / 'release/VERSION').read_text().strip()
REQUIRED = ('Audience', 'Purpose', 'Status', 'Release', 'Last Updated')
LINK = re.compile(r'(?<!!)\[[^\]]+\]\(([^)]+)\)')
HEADING = re.compile(r'^#{1,6}\s+(.+)$', re.M)
errors = synchronize(ROOT, VERSION, check=True)
files = sorted(p for p in ROOT.rglob('*.md') if not any(
    bit in  {'.git', '.venv', '.pytest_cache', 'node_modules', 'build', 'dist'}
    for bit in p.relative_to(ROOT).parts
))
for path in files:
    source = path.read_text(encoding='utf-8')
    relative = path.relative_to(ROOT)
    if not source.startswith('<!-- SPDX-License-Identifier: MIT -->'):
        errors.append(f'{relative}: missing SPDX header')
    for field in REQUIRED:
        pattern = rf'^\*\*{re.escape(field)}:\*\*\s+\S[^\n]*$'
        if not re.search(pattern, source, re.M):
            errors.append(f'{relative}: missing {field} metadata')
    if not re.search(
        rf'^\*\*Release:\*\* {re.escape(VERSION)}$',
        source, re.M
    ):
        errors.append(f'{relative}: release mismatch; expected {VERSION}')
    if not re.search(r'^# ', source, re.M):
        errors.append(f'{relative}: missing level-one title')
    # Markdown links in fenced examples are intentionally not navigational.
    no_fences = re.sub(r'^```[^\n]*\n.*?^```\s*$', '',
                       source, flags=re.M | re.S)
    for match in LINK.finditer(no_fences):
        dest = match.group(1).strip().split(' ', 1)[0].strip('<>')
        if not dest or dest.startswith(('https:', 'http:', 'mailto:')):
            continue
        target, _, anchor = unquote(dest).partition('#')
        resolved = (path.parent / target).resolve() if target else path
        if not resolved.is_relative_to(ROOT.resolve()) or not resolved.exists():
            errors.append(f'{relative}: missing linked file {dest}')
            continue
        if anchor and resolved.suffix.lower() == '.md':
            headings = HEADING.findall(resolved.read_text(encoding='utf-8'))
            slugs = set()
            for heading in headings:
                slug = re.sub(r'[^\w\- ]', '', heading.lower())
                slugs.add(re.sub(r' +', '-', slug.strip()))
            if anchor.lower() not in slugs:
                errors.append(f'{relative}: missing anchor {dest}')
    if relative == Path('INSTALLATION.md'):
        for invalid in ('/local/energy-usage-explorer',
                        '## Developer verification',
                        'python3 -m unittest', 'ha-energy-dev'):
            if invalid in source:
                errors.append(f'{relative}: developer-only wording: {invalid}')

# Public guidance must not assume a maintainer's private deployment.
PUBLIC_GUIDES = (
    'README.md', 'INSTALLATION.md', 'QUICKSTART.md',
    'docs/UPGRADING.md', 'docs/TROUBLESHOOTING.md',
)
PRIVATE_DEPLOYMENT = re.compile(
    r'\b(?:piha(?:-w)?|sparta|pme991|hass_homeassistant)\b'
    r'|/opt/homeassistant/config|docker service update --force',
    re.IGNORECASE,
)
for name in PUBLIC_GUIDES:
    content = (ROOT / name).read_text(encoding='utf-8')
    for match in PRIVATE_DEPLOYMENT.finditer(content):
        errors.append(f'{name}: private deployment reference: '
                      f'{match.group(0)}')

# Keep current navigation consistent in all maintained documentation.
OLD_NAVIGATION = re.compile(
    r'Developer [Tt]ools\s*(?:→|/)\s*(?:Statistics|Actions)'
    r'|Developer tools / Settings'
)
for path in files:
    for match in OLD_NAVIGATION.finditer(path.read_text(encoding='utf-8')):
        errors.append(f'{path.relative_to(ROOT)}: outdated menu: '
                      f'{match.group(0)}')

# Documentation describes only the current Home Assistant integration
# release. Do not mistake Home Assistant Core or Energy Ingest versions for
# this package's release; restrict the check to older 0.1.x references.
OLD_RELEASE = re.compile(r'(?<![\d.])v?0\.1\.(?:0|1)(?!\d)')
for path in files:
    for match in OLD_RELEASE.finditer(path.read_text(encoding='utf-8')):
        errors.append(f'{path.relative_to(ROOT)}: obsolete release: '
                      f'{match.group(0)}')

if errors:
    print('\n'.join(errors))
    raise SystemExit(f'Documentation: FAIL ({len(errors)} issues)')
print(f'Documentation: PASS ({len(files)} documents, release {VERSION})')
