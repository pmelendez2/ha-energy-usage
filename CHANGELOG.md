<!-- SPDX-License-Identifier: MIT -->
# Changelog

**Audience:** Users and administrators

**Purpose:** Changelog reference for Energy Usage.

**Status:** Published release history

**Release:** 0.1.3

**Last Updated:** 2026-10-29

## Unreleased

No changes recorded.

## 0.1.3 — Guided Utility Import (2026-11-03)

### Added

- Guided SDG&E Green Button XML import from individual files or folders.
- Utility Company selection with automatic single-company handling.
- Automatic Recorder synchronization for known physical meters.
- Explicit physical meter confirmation for unfamiliar reading resources.
- Commodity-aware electricity and natural gas meter selection.
- Plain-English import results for each XML file.
- Detection of previously imported XML files.
- Required-action warnings and interrupted-import recovery.
- Read-only Recorder verification utility.

### Improved

- Clear files removes selections, filenames, and previous results.
- Import progress and synchronization completion remain visible.
- Meter associations are verified before Recorder synchronization.
- Imported corrections update history without fabricating missing data.

### Requirements

- Energy Ingest 0.1.9 is required.

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
