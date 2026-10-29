<!-- SPDX-License-Identifier: MIT -->
# Home Assistant Integration Release Verification

**Audience:** Developers and maintainers

**Purpose:** Verify integration changes and prepare signed releases.

**Status:** Current documentation baseline

**Release:** 0.1.2

**Last Updated:** 2026-10-29

## Local verification

Run from the `ha-energy-usage` repository root:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m pytest -q
python3 -m compileall -q custom_components/energy_usage tests
python3 scripts/check_integration.py
python3 scripts/package_release.py --output /tmp/ha-energy-usage.zip
python3 scripts/check_release_package.py /tmp/ha-energy-usage.zip
node --check custom_components/energy_usage/www/energy-usage-explorer.js
node tests/test-energy-usage-explorer.cjs
python3 scripts/check_documentation.py
git diff --check
```

The CI `isolated` job runs the standard-library test and package checks;
`pytest` is an additional optional local check. The independent Python
compatibility matrix covers 3.13 and 3.14. Neither constitutes a real
Home Assistant runtime integration test.

## Development runtime acceptance

Test with a disposable Home Assistant instance, using the published
Energy Ingest HTTP API and a development-only bearer token. Confirm
successful setup, two meter devices, sensor state, failure/recovery,
and reload/unload.

Explicit initial Recorder imports have been runtime-validated. The v0.1.2
release also passed normal scheduled and manual synchronization tests in
development Home Assistant. These results do not establish completion of
all lifecycle, failure-recovery, or upgrade acceptance scenarios.
Verify that unload drains admitted synchronization work before runtime
cleanup, that temporary API failures do not write statistics, and that
subsequent cycles recover. Run these checks in disposable development HA;
unit tests alone do not establish live Recorder shutdown safety.

## Publishing

Use a feature branch and signed commits, then a pull request and required
CI checks before merging into protected `main`. GitHub release tags must
match the `manifest.json` version. For HACS installation use the GitHub
repository; the component-only ZIP is an optional manual-install artifact.

## 0.1.2 lifecycle and recovery acceptance checklist

The following scenarios remain acceptance criteria. Use disposable
Home Assistant and Energy Ingest environments:

- Verify configured startup delay and periodic scheduling with both meters.
- Start a synchronization, request config-entry unload, and verify that
  admitted work finishes persistence verification before runtime cleanup.
- Start manual and scheduled requests for the same meter; verify serialization.
- During a temporary Energy Ingest API outage, confirm no new Recorder rows
  are written and a later scheduled cycle recovers without fabricated data.
- Verify an accepted source correction updates the full cumulative series.
- Restart and reload repeatedly; check for duplicate listeners or stale locks.
- Upgrade an existing 0.1.1 development installation in place, preserving
  configuration, credentials, and historical Recorder statistics.
- Confirm INFO/DEBUG logs for normal events and ERROR logs for failures.

These are acceptance requirements, not claims of completed live testing.
The published v0.1.2 release does not establish completion of every live
failure-recovery or upgrade acceptance scenario.
