<!-- SPDX-License-Identifier: MIT -->
# Changelog

> **Audience:** Users and administrators
> **Purpose:** Changelog reference for Energy Usage.
> **Status:** Release candidate
> **Release:** 0.1.0
> **Last Updated:** 2026-10-23

## Unreleased

No changes documented since the initial release candidate.

## 0.1.0 — Initial release candidate

### Added

- Authenticated Energy Ingest meter discovery and diagnostic entities.
- Explicit guarded first-time import of accepted electricity and gas history
  into Home Assistant Recorder statistics.
- Electricity and gas compatibility with the built-in Energy Dashboard.
- Bundled Energy Usage Explorer charts, calendar navigation, calculations,
  and selection details, served by the integration's HTTP resource.
- Installation, tests, CI, HACS and hassfest validation.

### Limits

- Initial import does not append to or replace existing statistic series.
- Incremental synchronization and revision-aware corrections are not yet
  supported. Missing readings are never fabricated. No billing calculations.

**Publication:** Prepared for `v0.1.0`; verify release publication separately.
