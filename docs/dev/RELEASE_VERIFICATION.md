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
- Upgrade an existing installation to v0.1.2 in place, preserving
  configuration, credentials, and historical Recorder statistics.
- Confirm INFO/DEBUG logs for normal events and ERROR logs for failures.

These are acceptance requirements, not claims of completed live testing.
The published v0.1.2 release does not establish completion of every live
failure-recovery or upgrade acceptance scenario.

## ADR-0003 guided utility workflow runtime acceptance

Use an isolated Energy Ingest database and development Home Assistant. Before
each case record the integration commit, API image digest, Core version, and
Recorder row counts and hashes for both physical meters. Preserve the
original test XML privately; never attach credentials or customer XML.

1. Configure the integration. Confirm the setup review lists the physical
   meter IDs, commodities, and names returned by Energy Ingest. Confirm the
   options form shows the same authoritative inventory.
2. Upload electricity and gas XML. Inspect the import counters and returned
   resource IDs independently of association and Recorder results.
3. Repeat an unchanged XML import. Confirm identical resource IDs, no
   duplicate resources, and existing mappings preselected and locked.
4. Leave an unknown resource unselected. Confirm synchronization is blocked.
   Test two meters of the same commodity; no automatic choice is allowed.
5. Map an unassociated resource, then attempt a conflicting reassignment.
   The backend must retain its existing physical meter and Recorder must
   receive no history from the attempted conflicting mapping.
6. Interrupt the workflow after import, after partial association, and during
   Recorder synchronization. Restart Home Assistant each time. Confirm that
   the pending-resource journal allows safe recovery without XML persistence
   and that repeating the XML import remains idempotent.
7. Import multiple XML files with mixed outcomes. Verify that each filename
   has its own plain-English result, including previously imported files,
   accepted new or corrected readings, and unchanged usage data.
8. Verify that exact XML replays are identified using the canonical Energy
   Ingest `already_imported` result, not inferred from zero reading counts.
9. Verify that an import failure identifies the affected filename and that
   successfully processed earlier files remain listed.
10. Verify that the import summary remains visible after automatic Recorder
   synchronization and that physical meter names replace internal IDs.
11. Verify that an incompatible Energy Ingest API does not incorrectly report
   a file as previously imported.
12. Simulate API outage and recovery. Ensure the error stage is visible and
   no unverified success is reported. Retry only the affected meters.
13. Correct an existing observation and import actual readings for a formerly
   missing period. Confirm Recorder read-back reflects the supplied data and
   cumulative corrections, with no invented intermediate readings.
14. Verify that an administrator can upload and a nonadministrator receives
   HTTP 403. Confirm bounded upload sizes and no bearer tokens in card state.
15. Reload and upgrade the integration, preserving configured meters, pending
   resource IDs, authenticators, and existing Recorder statistics. Compare
   counts and hashes before and after each operation.

All cases require recorded pass/fail evidence before calling ADR-0003 runtime
accepted or deploying the development upload workflow to production.
