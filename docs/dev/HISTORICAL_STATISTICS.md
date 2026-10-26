<!-- SPDX-License-Identifier: MIT -->
<!-- AI-assisted: ChatGPT / GPT-6; 2026-10-16. -->

# Historical Statistics Development

> **Audience:** Developers and maintainers
> **Purpose:** Historical Statistics Development reference for Energy Usage.
> **Status:** Current documentation baseline
> **Release:** 0.1.0
> **Last Updated:** 2026-10-23

## Scope

The `custom_components/energy_usage/history.py` module normalizes
resolved observations from Energy Ingest. It does not write Home
Assistant Recorder statistics. Do not enable Energy Dashboard history
imports until correction, idempotency, and recovery tests are complete.

Electricity readings with unit code 72 represent Wh and require
conversion to kWh. Gas readings with unit code 169 represent therm;
apply the published measurement multiplier. Validate the source
period semantics before assigning daily gas statistics buckets.

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
- Persist synchronization progress only after successful Recorder writes.
- Reconcile corrections without double-counting or silently dropping data.
- Verify bucket semantics, gaps, and repeated imports with synthetic data.
- Exercise restart, reauthentication, and partial-failure recovery.

## Reference

- [Recorder statistics API changes](https://developers.home-assistant.io/blog/2025/10/16/recorder-statistics-api-changes/)
- [Home Assistant developer documentation](https://developers.home-assistant.io/)

## Recorder implementation verification checklist

These are development and test gates, not conditions for accepting ADR-0001.



Recorder writes remain disabled until the following interfaces and
behaviors have been established and tested:

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
