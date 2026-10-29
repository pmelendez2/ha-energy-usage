<!-- SPDX-License-Identifier: MIT -->
<!-- AI-assisted: ChatGPT / GPT-6; 2026-10-16. -->

# Historical Statistics Development

**Audience:** Developers and maintainers

**Purpose:** Recorder history behavior, evidence, and safe synchronization.

**Status:** Current documentation baseline

**Release:** 0.1.2

**Last Updated:** 2026-10-27

## Scope

The `custom_components/energy_usage/history.py` module normalizes
resolved observations from Energy Ingest without writing to Recorder.
The separately invoked initial-import service may enqueue validated
electricity and gas history into a previously empty statistic series.
That initial import was released in v0.1.0; it cannot append, replace,
or correct already-imported history. Automatic correction-safe
synchronization remains a separate, unimplemented capability.

Electricity readings with Green Button unit code 72 represent Wh
and are converted to kWh. Gas code 169 represents therm; apply the
source measurement multiplier. Never synthesize missing observations.

## API ownership and accepted observations

The Rust `energy_ingest` project owns the canonical usage model and its
versioned HTTP API. It is the source of truth for the API contract and
any generated OpenAPI specification. This Home Assistant integration
consumes its authenticated, accepted readings and tests the response
shapes it needs; it must not publish a conflicting server schema.
API contract documentation and an optional development Swagger UI
belong in `energy_ingest`, without exposing tokens or privileged actions.

## Local date ranges and natural gas reporting

Home Assistant's configured time zone determines the inclusive local
calendar dates selected for import. Query boundaries are converted to UTC
internally. Daylight-saving changes may result in 23- or 25-hour local
days; never assume every local day lasts 86,400 seconds.

SDG&E natural gas downloads observed in October 2026 label a daily
reading at **11:59 PM Pacific time** with a fixed 86,400-second source
duration. For Recorder display, Energy Usage assigns the observed
consumption to midnight on that same **local reporting date**. This
is a presentation convention, not a change to the source timestamp,
period, or quantity. The converter rejects unrecognized gas reporting
boundaries rather than guessing their meaning. Missing reporting dates
remain absent, including across daylight-saving transitions.

The initial import uses bounded API date/time range requests, with a
maximum of 31 days per request. The complete-range button determines the
range from the accepted stream, then retrieves the supported windows.
Do not run a short initial import expecting to extend that statistic
with another initial-import request.

## Recorder write and retry boundaries

`async_add_external_statistics` submits a job to Recorder's asynchronous
queue. Submission is not proof that data was committed. Verify the
stored statistic in Home Assistant's Statistics tools before declaring
the import complete. The v0.1.1 import guard blocks another submission
while a previous one could still be pending. A safe retry after a failed
queued write requires confirmation that no history persisted and a Home
Assistant restart to clear the old in-process queue. Never delete
existing statistics to make the first-time importer run again.

## Development verification

Run from the `ha_energy_usage` repository root:

```bash
python3 -m unittest discover -s tests -p 'test_history.py' -v
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

The tests validate normalization and simulated integration behavior;
they do not establish Home Assistant Recorder runtime compatibility.

## Required integration behavior

- Retrieve bounded, server-resolved meter observations over UTC windows.
- Refuse unresolved, contradictory, or incomplete measurements.
- Use stable statistic identifiers per physical meter and commodity.
- Persist future synchronization progress only after verified Recorder
  writes; initial-import queuing is not such a checkpoint.
- Reconcile corrections without double-counting or silently dropping data.
- Verify bucket semantics, gaps, and repeated imports with synthetic data.
- Exercise restart, reauthentication, and partial-failure recovery.

## Reference

- [Recorder statistics API changes](https://developers.home-assistant.io/blog/2025/10/16/recorder-statistics-api-changes/)
- [Home Assistant developer documentation](https://developers.home-assistant.io/)

## Recorder implementation verification checklist

These are development and test gates, not conditions for accepting ADR-0001.

**Automatic synchronization and correction/rebuild writes** remain
disabled until the following interfaces and behaviors are established
and tested. This does not prohibit the guarded initial import:

- The exact Home Assistant Core version and supported statistics update and
  correction API; whether external statistics are eligible for the desired
  Energy Dashboard electricity and gas configuration.
- The stable statistic ID format and its ownership/migration behavior.
- Provider gas day boundaries and daily consumption representation,
  including DST transitions.
- How a correction or late reading updates subsequent cumulative sums
  without filling gaps or overwriting unrelated Recorder series.
- The checkpoint and restart-recovery location, write-completion semantics,
  and handling of a successful Recorder write followed by a crash.
- The explicit user controls for enabling initial backfill and subsequent
  synchronization, and how failures or partial coverage are reported.
- The exact supported strategy for scoped statistics repair/rebuild, including
  how to identify and replace corrupt values without collateral deletion,
  and how write completion and interruption recovery are verified.
- Source-cadence support and coverage checks for 15-minute intervals; test
  incomplete hours and daylight-saving transitions.
