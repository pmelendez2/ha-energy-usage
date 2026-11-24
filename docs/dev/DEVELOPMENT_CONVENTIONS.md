<!-- SPDX-License-Identifier: MIT -->
# Development and documentation conventions

**Audience:** Developers and maintainers

**Purpose:** Define the shared project documentation rules.

**Status:** Current documentation baseline

**Release:** 0.1.5

**Last Updated:** 2026-11-24

## Conventions

- Use MIT SPDX notices and a single top-level title.
- Put Audience, Purpose, Status, Release, and Last Updated metadata after it.
  Each field must appear in its own plain Markdown paragraph, without
  blockquote markup, so the UI renders one field per line.
- Distinguish documentation baseline from actual GitHub publication status.
- Keep production installation in the repository root and user
  troubleshooting in `docs/TROUBLESHOOTING.md`.
- Keep implementation, tests, and release verification under `docs/dev/`.
- Retain current developer procedures and durable technical decisions.
  Remove obsolete implementation-chunk reports once relevant behavior
  is covered by source tests, ADRs, or current development guidance.
- Keep test strategy and test evidence under `docs/testing/`.
- Keep decisions under `docs/adr/`; preserve decision dates and identifiers.
- Use working relative Markdown links and prefer audience-appropriate targets.
- Retain historical release entries; current metadata identifies the baseline.
- Align terminology with [Terminology](../TERMINOLOGY.md) and UI localization
  policy with [Internationalization](I18N.md).
- Run `python3 scripts/check_documentation.py` on every change.
It checks all Markdown metadata, local links, current release
statements, directory placement, portable installation commands,
and dashboard setup guidance. The policy has unit tests in
`tests/test_doc_policy.py`, runs in isolated CI, and is required
by `scripts/check-publication.sh`. Keep checks tied to actual
release files, not a maintainer’s local host or directory.

## Version markers

The current Home Assistant integration version comes from
`release/VERSION`; the recommended Energy Ingest backend version
comes from `release/ENERGY_INGEST_VERSION`. These are different
products with independent release cycles.

Current version references in maintained user guides are enclosed
in `current-version:ha-energy-usage` and
`current-version:energy-ingest` markers, with matching
closing markers. These HTML comments are invisible in rendered
Markdown. Historical versions in ADRs, CHANGELOG.md and dated
testing evidence must not be rewritten automatically.

Run `python3 scripts/manage_doc_versions.py --check` to verify
markers. After updating `release/ENERGY_INGEST_VERSION`, run
`python3 scripts/manage_doc_versions.py --sync` to update only
marked references. Or use
`python3 scripts/manage_doc_versions.py --set-energy-ingest X.Y.Z`.
When updating the integration release with
`python3 scripts/update_documentation_version.py --set X.Y.Z`,
current-version markers are also synchronized. Check other
release-dependent prose manually before publishing.
