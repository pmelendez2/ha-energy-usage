<!-- SPDX-License-Identifier: MIT -->
# Development and documentation conventions

> **Audience:** Developers and maintainers
> **Purpose:** Define the shared project documentation rules.
> **Status:** Current documentation baseline
> **Release:** 0.1.0
> **Last Updated:** 2026-10-23

## Conventions

- Use MIT SPDX notices and a single top-level title.
- Put Audience, Purpose, Status, Release, and Last Updated metadata after it.
- Distinguish documentation baseline from actual GitHub publication status.
- Keep production installation and troubleshooting in the repository root.
- Keep implementation, tests, and release verification under `docs/dev/`.
- Keep test strategy and test evidence under `docs/testing/`.
- Keep decisions under `docs/adr/`; preserve decision dates and identifiers.
- Use working relative Markdown links and prefer audience-appropriate targets.
- Retain historical release entries; current metadata identifies the baseline.
- Align terminology with [Terminology](TERMINOLOGY.md) and UI localization
  policy with [Internationalization](I18N.md).
- Run `python3 scripts/check_documentation.py` before each release.
