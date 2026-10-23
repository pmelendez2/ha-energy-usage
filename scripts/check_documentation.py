#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check documentation metadata, local links, and release consistency."""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'custom_components/energy_usage/manifest.json'
VERSION = json.loads(MANIFEST.read_text())['version']
REQUIRED = ('Audience', 'Purpose', 'Status', 'Release', 'Last Updated')
LINK = re.compile(r'(?<!!)\[[^\]]+\]\(([^)]+)\)')
HEADING = re.compile(r'^#{1,6}\s+(.+)$', re.M)
errors = []
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
        if f'> **{field}:**' not in source:
            errors.append(f'{relative}: missing {field} metadata')
    if f'> **Release:** {VERSION}' not in source:
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

if errors:
    print('\n'.join(errors))
    raise SystemExit(f'Documentation: FAIL ({len(errors)} issues)')
print(f'Documentation: PASS ({len(files)} documents, release {VERSION})')
