<!-- SPDX-License-Identifier: MIT -->
# Publishing Energy Usage for Home Assistant

**Audience:** Developers and maintainers

**Purpose:** Publishing Energy Usage for Home Assistant reference for Energy Usage.

**Status:** Current documentation baseline

**Release:** 0.1.5

**Last Updated:** 2026-11-23

`ha-energy-usage` is a custom integration, not part of Home Assistant Core.

1. Run local tests and GitHub Actions, including supported Home Assistant
   versions. Do not claim a version is tested without completing runtime tests.
2. Create a signed commit on a feature/fix branch and merge through a PR
   after required `isolated`, HACS, Hassfest, and compatibility checks.
   Do not push source changes directly to protected `main`.
3. Create a signed version tag matching `release/VERSION` and
   `custom_components/energy_usage/manifest.json`; publish a full GitHub
   Release with release notes and verified artifacts.
4. The integration is in the default HACS catalog. Test installation by
   searching for **Energy Usage** in HACS, without a custom repo step.
5. For manual installation, copy `custom_components/energy_usage/` into
   Home Assistant's `custom_components/` directory and restart.

Local images under `custom_components/energy_usage/brand/` are included
in the repository. HACS default-catalog acceptance was confirmed by
[hacs/default PR #13425](https://github.com/hacs/default/pull/13425),
merged November 9, 2026; this is not Home Assistant Core inclusion.

The maintainer's [HACS submission checklist](HACS_SUBMISSION.md)
records the completed catalog application and remaining runtime checks.

**Current limitations:** Explicit initial Recorder import is supported
for previously empty statistic series. Correction-safe synchronization is
available, while full lifecycle and failure-recovery runtime acceptance
remains outstanding. Solar production/export ingestion is out of scope.

## Release gates

- Verify Python and bundled Explorer tests, package contents, and documentation links.
- Run HACS Action and hassfest without ignored failures.
- Confirm `manifest.json` version matches the intended signed release tag.
- Publish a **full GitHub Release**, not only a Git tag.
- Test a default HACS catalog download for every release candidate.
