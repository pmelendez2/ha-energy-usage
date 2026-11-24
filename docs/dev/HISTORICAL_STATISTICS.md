<!-- SPDX-License-Identifier: MIT -->
<!-- AI-assisted: ChatGPT / GPT-6; 2026-10-16. -->

# Historical Statistics Development

**Audience:** Developers and maintainers

**Purpose:** Recorder history behavior, evidence, and safe synchronization.

**Status:** Current documentation baseline

**Release:** 0.1.5

**Last Updated:** 2026-11-23

## Scope

The `custom_components/energy_usage/history.py` module normalizes
resolved observations from Energy Ingest without writing to Recorder.
The separately invoked initial-import service may enqueue validated
electricity and gas history into a previously empty statistic series.
The initial import action cannot append, replace,
or correct already-imported history. The separate correction-safe
synchronization service is implemented in v0.1.5, supports accepted
corrections, and remains opt-in for recurring scheduled execution.
Full production failure-recovery acceptance is tracked separately.

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
the import complete. The import guard blocks another submission
while a previous one could still be pending. A safe retry after a failed
queued write requires confirmation that no history persisted and a Home
Assistant restart to clear the old in-process queue. Never delete
existing statistics to make the first-time importer run again.

## Development verification

Run from the `ha-energy-usage` repository root:

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

## Recorder verification

Recorder synchronization, correction, and scoped repair must pass source-level
regression tests and the applicable live Home Assistant runtime acceptance
checks before claiming complete production verification. The requirements,
exact test commands, and unautomated scenarios are maintained in
[the Test Plan](../testing/TEST_PLAN.md#recorder-runtime-acceptance-matrix).
See [Release Verification](RELEASE_VERIFICATION.md) for current repository
verification procedures and
[Tested Environments](../testing/TESTED_ENVIRONMENTS.md) for recorded live
results and outstanding limitations. The architecture is defined in
[ADR-0001](../adr/0001-historical-utility-usage-recorder-synchronization.md).
An accepted ADR is not proof of completed runtime acceptance.

## Utility XML upload and reconciliation (development)

Home Assistant exposes an authenticated XML upload endpoint at
`POST /api/energy_usage/utility_upload?source_id=<ID>&sync=1`.
The endpoint forwards a single bounded Green Button XML document (8 MiB
maximum) to Energy Ingest using the configured API token. The source ID
identifies an acquisition source, not a physical meter. The XML is not
persisted by the Home Assistant view. Canonical import commits before
Recorder synchronization, so a failed synchronization is separately
retryable and must never be reported as a failed canonical import.
The Utility Card is included in published v0.1.5. Do not expose the
upload endpoint through an unauthenticated proxy. Verify authorization,
multi-file behavior, and failure recovery in production deployments.
