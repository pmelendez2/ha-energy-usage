<!-- SPDX-License-Identifier: MIT -->
# Changelog

**Audience:** Users and administrators

**Purpose:** Changelog reference for Energy Usage.

**Status:** Published release history

**Release:** 0.1.2

**Last Updated:** 2026-10-29

## Unreleased

No changes recorded.

## 0.1.2 — Correction-Safe Synchronization (2026-10-28)

### Changed

- Drain admitted scheduled and manual synchronization operations during
  configuration-entry unload before releasing shared meter locks.
- Prevent new synchronization operations after runtime shutdown begins.
- Normalize routine scheduler and persistence logging levels.
- Add regression tests for shutdown draining and transient API failures.
- Preserve complete canonical Recorder read-back and correction safeguards.
- Keep initial import separate from recurring correction-safe synchronization.
- Update README, installation, and developer verification guidance for
  the published release and outstanding runtime acceptance.
- Document remaining live lifecycle, recovery, and upgrade acceptance
  scenarios without claiming they have passed.


### Included capabilities

- Guided, per-meter first-time import with discovered local-calendar coverage.
- Authenticated meter discovery, import diagnostics, and Energy Dashboard data.
- Bundled Energy Usage Explorer with calendar navigation and details.
- Recorder-aware pending-import checks and correction-safe synchronization.
- Missing consumption observations remain missing; billing is out of scope.
