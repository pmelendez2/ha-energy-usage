<!-- SPDX-License-Identifier: MIT -->
# Changelog

**Audience:** Users and administrators

**Purpose:** Changelog reference for Energy Usage.

**Status:** Release candidate

**Release:** 0.1.2

**Last Updated:** 2026-10-29

## Unreleased

### In development for 0.1.2

- Drain admitted scheduled and manual synchronization operations during
  configuration-entry unload before releasing shared meter locks.
- Prevent new synchronization operations after runtime shutdown begins.
- Normalize routine scheduler and persistence logging levels.
- Add regression tests for shutdown draining and transient API failures.
- Preserve complete canonical Recorder read-back and correction safeguards.
- Keep initial import separate from recurring correction-safe synchronization.
- Update README, installation and developer verification guidance to reflect
  the development implementation and its outstanding runtime acceptance.
- Clarify that unload/reload, Recorder shutdown, API recovery and production
  upgrade acceptance are not yet verified in live Home Assistant.


### Planned for 0.1.1

- One-click, per-meter initial import of complete verified historical data.
- Automatic discovery of the meter's actual local-calendar coverage.
- Clearer duplicate-import rejection and a concise installation quick start.
- Recorder-aware pending-import checks with safe retry guidance after restart;
  no retry while an earlier asynchronous write may still be queued.
- HACS default-catalog submission readiness checklist.
- Per-meter historical import status, verified against persisted Recorder
  statistics, with the last in-session attempt and any error reported.
- Last import attempt and last import error are visible as separate
  per-meter diagnostic sensors; no developer tools needed.

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
