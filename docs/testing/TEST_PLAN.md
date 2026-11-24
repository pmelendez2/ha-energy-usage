<!-- SPDX-License-Identifier: MIT -->
# Test Plan

**Audience:** Maintainers and contributors

**Purpose:** Test Plan reference for Energy Usage.

**Status:** Current documentation baseline

**Release:** 0.1.5

**Last Updated:** 2026-11-24

The recorded verification matrix and its evidence are maintained in
[Tested Environments](TESTED_ENVIRONMENTS.md).

## Recorded development environments

- An early test used Home Assistant Core 2026.9.4 and
  Frontend 20260826.7 on Ubuntu 26.04.
- Later development smoke tests used Home Assistant Container
  Core 2026.10.1. See [Tested Environments](TESTED_ENVIRONMENTS.md) for exact evidence.
- These are historical test configurations, not a promise of
  compatibility with every future Home Assistant version.

## Release validation

For each Home Assistant release considered for support:

1. Run the automated test suite.
2. Run the Home Assistant compatibility test matrix.
3. Perform a Container-based smoke test when required.
4. Verify electricity statistics.
5. Verify gas statistics.
6. Verify Energy Dashboard behavior.
7. Record known compatibility issues.
8. Add the verified environment and its evidence to
   [Tested Environments](TESTED_ENVIRONMENTS.md).
9. Update any user-facing compatibility summary only after recording evidence.

## Recorder runtime acceptance matrix

Recorder requirements are defined by
[ADR-0001](../adr/0001-historical-utility-usage-recorder-synchronization.md).
The Python tests below verify source-level contracts or simulated Recorder
behavior; they do **not** demonstrate compatibility with a running Home
Assistant Recorder or an actual Energy Ingest API. Live acceptance must use
an isolated Home Assistant instance and Energy Ingest database, record the
precise Core/API versions, and publish pass/fail evidence in
[Tested Environments](TESTED_ENVIRONMENTS.md).

Run the complete automated suite from the repository root:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

For focused Recorder source-level tests:

```bash
python3 -m unittest discover -s tests -p 'test_statistics_adr0001.py' -v
python3 -m unittest discover -s tests -p 'test_statistics_sync_gap_acceptance.py' -v
python3 -m unittest discover -s tests -p 'test_statistics_sync_recorder.py' -v
python3 -m unittest discover -s tests -p 'test_statistics_sync_verify.py' -v
python3 -m unittest discover -s tests -p 'test_sync_gas_recorder_boundary.py' -v
```

| Acceptance requirement | Automated source-level coverage | Live verification still required |
| --- | --- | --- |
| Verify the exact supported Home Assistant Core statistics update/correction APIs and Energy Dashboard electricity/gas eligibility. | `tests/test_statistics_sync_recorder.py` | Yes: actual Core statistics interfaces and dashboard selection. |
| Keep statistic IDs stable by physical meter/commodity; define safe ownership and migration when semantics change. | `tests/test_statistics_adr0001.py`, `tests/test_statistics_sync_recorder.py` | Yes: existing history and upgrades with real Recorder data. |
| Map provider daily gas reporting dates accurately across DST transitions. | `tests/test_sync_gas_recorder_boundary.py`, `tests/test_statistics_sync_verify.py` | Yes: actual provider periods and local dashboard dates. |
| Reconcile corrections and late readings, recomputing cumulative totals without filling gaps or modifying unrelated series. | `tests/test_statistics_sync_gap_acceptance.py`, `tests/test_statistics_sync_verify.py` | Yes: real Recorder read-back after correcting earlier data. |
| Verify queued writes, checkpoint timing, restart/recovery and a crash following a successful Recorder write. | `tests/test_statistics_sync_verify.py`, `tests/test_statistics_sync_recorder.py` | Yes: restart/crash tests and persistence confirmation; not replaced by unit mocks. |
| Verify explicit user opt-in for initial import and scheduled synchronization, including failure/partial-coverage reporting. | `tests/test_statistics_sync_recorder.py`, `tests/test_sync_opt_in_v015.py` | Yes: controls, reload, scheduler, and operator-facing status. |
| Verify safe, scoped statistics repair/rebuild without deleting unrelated history, including interruption and completion verification. | `tests/test_statistics_sync_verify.py` (read-back and consistency aspects) | Yes: full repair/rebuild dry-run, interrupted write, and scoped recovery. |
| Validate 15-minute source cadence, complete-hour coverage, missing/incomplete hours, and DST transitions. | `tests/test_statistics_adr0001.py`, `tests/test_statistics_sync_gap_acceptance.py` | Yes: canonical input, UTC/local bounds and real Recorder presentation. |

These items are release acceptance requirements, not claims that every live
scenario has already passed. Record the tested versions, commands, observed
Recorder counts and outcome for each runtime case. Do not store customer XML
or bearer tokens in committed evidence.

## Lifecycle and recovery runtime acceptance

The following are required live runtime scenarios. Execute them in
disposable Home Assistant and Energy Ingest environments; source-level
unit tests alone do not establish their completion. Record the exact
versions and per-case outcomes in
[Tested Environments](TESTED_ENVIRONMENTS.md).

- Verify configured startup delay and periodic scheduling with both meters.
- Start a synchronization, request config-entry unload, and verify that
  admitted work finishes persistence verification before runtime cleanup.
- Start manual and scheduled requests for the same meter; verify serialization.
- During a temporary Energy Ingest API outage, confirm no new Recorder rows
  are written and a later scheduled cycle recovers without fabricated data.
- Verify an accepted source correction updates the full cumulative series.
- Restart and reload repeatedly; check for duplicate listeners or stale locks.
- Upgrade an existing installation to the current release in place, preserving
  configuration, credentials, and historical Recorder statistics.
- Confirm INFO/DEBUG logs for normal events and ERROR logs for failures.

## ADR-0003 runtime acceptance scenarios

These scenarios implement the behavior defined by
[ADR-0003](../adr/0003-guided-physical-meter-mapping-and-import-synchronization.md).
Existing Python contract and regression tests cover parts of these
requirements but are not an automated end-to-end Home Assistant runtime
acceptance harness.

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

Record outcomes as pass/fail/not-run for each target runtime environment.
The ADR remains Accepted independently of runtime verification status.

## Exit criteria

A Home Assistant version must not be listed as tested until the defined
compatibility tests have completed successfully.
