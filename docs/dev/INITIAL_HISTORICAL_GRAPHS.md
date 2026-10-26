<!-- SPDX-License-Identifier: MIT -->
# Initial historical usage graphs — development milestone

> **Audience:** Developers and maintainers
> **Purpose:** Initial historical usage graphs — development milestone reference for Energy Usage.
> **Status:** Current documentation baseline
> **Release:** 0.1.0
> **Last Updated:** 2026-10-23

**Status:** Implemented initial-import capability (0.1.0). **Purpose:** Import actual utility-provided usage history into Home Assistant's statistics system so its Energy Dashboard can graph existing electricity and natural gas readings. **Intended audience:** Energy Usage developers and testers.

## Definitions

- **Date range:** Calendar dates selected by the customer. The first and last dates are included. Energy Usage interprets both selected dates in the configured Home Assistant time zone, then converts the boundaries to UTC internally. Customers never enter timestamps.
- **Reading:** A utility-provided measurement of actual electricity or gas consumption for a particular period.
- **Historical statistic:** A stored Home Assistant observation used in long-term graphs and the Energy Dashboard.
- **Missing reading:** A time period for which the utility has provided no accepted observation. Missing information must not be estimated or filled.
- **Initial import:** First-time creation of a new, previously empty historical statistic. It is **not** a repair or correction of an existing series.
- **Correction:** A revised utility reading for a period previously published. Correcting Recorder statistics safely is outside this milestone.

## Calendar-date example

A customer selecting October 1 through October 7, 2026 in a Home Assistant instance set to `America/Los_Angeles` requests all seven local calendar days. Energy Usage converts that selection to the UTC interval beginning October 1 at 07:00 UTC and ending October 8 at 07:00 UTC. These timestamps are internal and are not entered by the customer.

## What is included

This milestone adds `energy_usage.import_historical_usage`, an explicitly invoked, initial-import-only Home Assistant action. The action retrieves actual accepted readings from Energy Ingest in API requests of no more than 31 days each, verifies units and periods, and prepares cumulative statistics. It uses Home Assistant's supported Recorder external-statistics API.

The action never starts automatically. It refuses an existing statistic series and refuses missing, ambiguous, incompatible, overlapping, or negative consumption data. It does **not** delete or rewrite Recorder data, estimate readings, calculate billing, or change utility source data.

**Important:** A graph of imported rows is not evidence that full-history correction synchronization works. A later milestone must add revision-aware, read-back-verified, safely replaceable statistics and automatic change discovery. A statistics write is queued; successful persistence must be checked in Home Assistant's statistics tools.

## Isolated runtime verification workflow

1. Deploy only to the isolated `ha-energy-dev` container on `sparta`; keep production HA unchanged. Ensure its API URL and bearer token already work and point to the existing Energy Ingest installation.
2. Confirm the physical meter identifier using Energy Ingest's existing meter inventory. Check its validated stream results before proceeding.
3. Back up the **development** Recorder database before importing. Start with a short date range for one meter.
4. In Home Assistant **Developer tools → Actions**, choose `energy_usage.import_historical_usage`. Supply:

   ```yaml
   meter_id: 1
   start_date: '2026-10-01'
   end_date: '2026-10-07'
   confirm_initial_import: true
   ```

   **Example only:** meter IDs must be discovered; do not assume `1` refers to electricity on another installation.
5. Open **Developer tools → Statistics** and find `energy_usage:electricity_meter_1` (or `energy_usage:gas_meter_2` for a gas meter). Verify date coverage and values before using it in the Energy Dashboard.
6. In **Settings → Dashboards → Energy**, select the imported statistics series for Grid consumption or Gas consumption. The dashboard will render graphs for the imported date range. A new development series may appear only after Recorder processes its queued import.

## Known limits and cautions

- Because the importer deliberately refuses to modify an existing statistic, **do not start with a short trial import and then expect a second import to extend that same series**. To graph the full year in one go, use a fresh development Recorder instance and request the complete known utility coverage, after testing in a disposable instance.
- A long date range may be rejected if any individual API range cannot be resolved, or if the observations do not meet the expected hourly electricity / daily gas cadence. This prevents misleading graphs.
- Selected dates use the configured Home Assistant time zone (for example, `America/Los_Angeles`). The start and end dates are included. The conversion correctly handles 23- and 25-hour daylight-saving days; do not assume each calendar day has 24 hours.
- Energy Ingest stores observations with their original timestamps. Converting a customer's selected dates changes query boundaries only; it does not shift, rewrite, invent, or change utility measurements. Daily gas readings whose boundaries differ from local midnight still require careful end-to-end acceptance testing before importing.
- Only one configured Energy Usage instance is currently supported by this service. Production initial imports must target a previously empty series; do not use the action for recurring updates or with multiple configuration entries.
- Missing periods are not represented by invented readings. Home Assistant graph rendering of cumulative statistics may connect distant actual points; do not interpret a connected line as proof that missing hours have been filled.
- No billing amount, solar monetary value, or estimated consumption is generated.
- Energy Ingest validates accepted readings before the Home Assistant import. Consult the Energy Ingest architecture decisions in its own repository for ingestion and canonical-data policy.

## Developer checks

Run `python3 -m unittest discover -s tests -p 'test_*.py'`, `python3 -m compileall -q custom_components/energy_usage tests`, and the repository's integration and release-package checks. Review Home Assistant logs and Recorder read-back in the isolated development system before proposing a release.

**AI assistance:** Drafted with ChatGPT GPT-6 on 2026-10-21. Human review, HA runtime validation, and release approval required.

## SDG&E natural gas reporting dates

SDG&E daily gas exports observed in October 2026 label readings at 11:59
PM Pacific time and use a fixed 86,400-second duration. For graphs,
Energy Usage places that daily amount at midnight on the same **local
reporting date**. This is an explicitly approximate display convention;
it does not alter the source timestamp or consumption amount. Missing
local calendar dates remain absent. This convention is intended for
trend viewing, **not billing reconciliation**.

The statistics converter rejects other unrecognized daily reporting times
rather than silently guessing. The initial-import service supplies Home
Assistant's configured time zone to the converter. Initial imports are
still guarded and cannot repair an existing Recorder statistics series.
