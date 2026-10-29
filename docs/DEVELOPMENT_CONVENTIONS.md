<!-- SPDX-License-Identifier: MIT -->
# Development and documentation conventions

**Audience:** Developers and maintainers

**Purpose:** Define the shared project documentation rules.

**Status:** Current documentation baseline

**Release:** 0.1.2

**Last Updated:** 2026-10-27

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
- Align terminology with [Terminology](TERMINOLOGY.md) and UI localization
  policy with [Internationalization](I18N.md).
- Run `python3 scripts/check_documentation.py` before each release.
