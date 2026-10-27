<!-- SPDX-License-Identifier: MIT -->
# Changelog

**Audience:** Users and administrators

**Purpose:** Changelog reference for Energy Usage.

**Status:** Release candidate

**Release:** 0.1.1

**Last Updated:** 2026-10-23

## Unreleased

### Planned for 0.1.1

- One-click, per-meter initial import of complete verified historical data.
- Automatic discovery of the meter's actual local-calendar coverage.
- Clearer duplicate-import rejection and a concise installation quick start.
- Recorder-aware pending-import checks with safe retry guidance after restart;
  no retry while an earlier asynchronous write may still be queued.
- HACS default-catalog submission readiness checklist.

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
