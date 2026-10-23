<!-- SPDX-License-Identifier: MIT -->
# 0001. Historical utility usage synchronization with Recorder

> **Audience:** Maintainers and contributors
> **Purpose:** 0001. Historical utility usage synchronization with Recorder reference for Energy Usage.
> **Status:** Current documentation baseline
> **Release:** 0.1.0
> **Last Updated:** 2026-10-23

* Status: Accepted
* Date: 2026-10-19

## Context

`ha_energy_usage` provides a Home Assistant interface to the separately
maintained `energy_ingest` service. The service persists actual Green Button
observations, accepted revisions, physical meter associations, and retrieval
history. Home Assistant Recorder stores statistics used by the Energy
Dashboard; registering a current-value sensor alone does not backfill past
utility usage.

The integration already has authenticated API access, bounded UTC history
retrieval, strict unit normalization, and a reconciliation planner. Those
modules do not write Recorder statistics. Historical imports must preserve
missing data and handle corrections without double-counting.

The repositories are independently released. The integration must not depend
on direct access to `energy_ingest` MariaDB or its source checkout.

## Decision

### Authority and boundaries

1. `energy_ingest` remains the authority for actual utility observations,
   accepted revisions, source identity, and physical meter mapping.
2. `ha_energy_usage` consumes resolved data through the authenticated,
   bounded Energy Ingest API. It never connects directly to MariaDB.
3. Home Assistant Recorder is a **derived reporting store**, not another
   source of utility truth. Use supported Home Assistant statistics interfaces,
   not direct Recorder SQL writes.
4. Currently, the integration supports electricity and natural-gas
   **consumption** and usage history. Billing, currency values, rates,
   credits, and solar sell-back payments are not supported at present.
   Future capabilities require separate decisions and validation. Never
   fabricate utility-provided observations; any future forecasts must be
   explicitly identified as derived estimates, not actual usage.

### Physical meters and statistic identities

5. Publish separate statistics per confirmed physical meter and commodity
   (currently Electricity or Natural Gas), never per XML file or mutable
   display name. Identifiers must remain stable
   across restarts, reimports, and friendly-name changes. Do not publish an
   unconfirmed resource-to-meter association.
6. A change in physical meter identity or measurement semantics must not
   silently reuse an existing statistic identifier. Define a migration or
   explicitly create a distinct series after review.

### Measurements, time and gaps

7. Preserve interval start, duration, accepted revision, and UTC provenance
   while normalizing. Green Button ESPI unit-of-measure code 72 means Wh
   and code 169 means therm; these are standard codes, not SDG&E-specific.
   Apply the supplied power-of-ten multiplier. Currently supported output
   is kWh (for electricity) and therm (for gas). Additional units require
   explicit, tested conversion; never infer units solely from commodity.
8. Accept actual electricity intervals at verified source cadences,
   including 15-minute and hourly readings. Aggregate to an hourly
   statistic only when nonoverlapping source observations exactly cover
   the entire hour. Do not publish an incomplete hour as a complete total.
   Reject ambiguous overlap, duplicate values, incompatible boundaries,
   and invalid readings. Preserve source-resolution observations in
   Energy Ingest; do not synthesize missing intervals.
9. Daily gas readings must **not** be treated as UTC-calendar-day or hourly
   readings until their provider period boundaries, daylight-saving behavior,
   and Home Assistant statistics representation are tested. No hourly gas
   allocation, interpolation, or assumed start-of-day time is permitted.
10. Missing periods remain missing, including isolated hours and entire days
    or months. Zero is a valid observed value only if supplied by the
    provider; never insert zero or carry readings forward to conceal a gap.
    Show incomplete coverage explicitly where the dashboard supports it;
    otherwise do not describe partial totals as complete.

### Synchronization, correction and recovery

11. A synchronized series must be deterministic: repeating the same accepted
    input yields the same published statistics. Do not append duplicates.
12. Later actual observations for previously missing periods are accepted.
    Accepted corrections replace the corresponding derived consumption and
    recompute dependent cumulative sums from a verified earlier anchor.
    Revision-ID-only changes that leave usage identical do not change totals.
13. When the API returns observations for a specified start/end time range
    (a bounded response), an absent previously imported observation is
    not by itself evidence of deletion. Deletion or reshaping requires an
    explicit, verified correction policy; never delete merely because a
    partial response omits an observation.
14. Validate a complete affected range before publishing. Fail closed for
    unresolved intervals, inconsistent units, overlapping durations,
    invalid values, unexpected upstream data, or incomplete required context.
15. Persist a synchronization checkpoint only **after** the Recorder operation
    has completed successfully and its intended result can be verified.
    Retries after interruption must reconcile current Recorder state, not
    blindly append results. Preserve enough local state to detect changes in
    previously processed windows, including historical corrections.
16. Do not mutate Recorder history during config flow, diagnostic polling,
    or routine source validation. Historical synchronization is a separately
    controlled operation with observable success/failure status.
17. Support administrator-initiated rebuilding of integration-owned Recorder
    statistics from accepted Energy Ingest observations without requiring a
    full Home Assistant or database restore. Before altering data, validate
    meter identity, requested time span, complete upstream availability,
    units, coverage, and statistics ownership. Scope replacement strictly to
    this integration's statistic identifiers; never clear unrelated history.
    Take a recommended backup, present a dry-run impact summary, obtain
    confirmation, and verify results after writes finish. Do not publish
    partial reconstruction as a completed repair. Handle interruption with
    restart-safe retry and comparison against Recorder state.

### Home Assistant compatibility and tests

18. Use Home Assistant's supported external-statistics or import-statistics
    APIs appropriate to the installed Core version. Statistics metadata must
    include the supported `mean_type` and `unit_class` fields, rather than
    relying on deprecated `has_mean` behavior. Exact API behavior and
    correction semantics must be verified against the development runtime.
19. Automated tests must cover initial backfill, repeat runs, absent hours,
    zero observations, late arrivals, corrected older observations,
    changed duration, unit rejection, DST boundaries, missing meter mapping,
    partial failures, restart recovery, authentication failures,
    15-minute aggregation, incomplete-hour rejection, and safe full or
    time-range reconstruction after missing/corrupt Recorder statistics.
20. Validate on the existing `sparta` Home Assistant development instance
    before any deployment to production `piha`; do not modify the existing
    production Home Assistant or Frigate deployments as part of development.

## Consequences

- The Energy Dashboard can eventually display historical usage without
  importing artificial historical entity states.
- `energy_ingest` and `ha_energy_usage` remain independently deployable.
- Data accuracy, explicit coverage gaps, and revision-safe recovery take
  precedence over a visually continuous dashboard.
- The integration needs a durable, meter-scoped synchronization strategy,
  runtime-compatible Recorder adapter, and failure/restart tests.
- A full history rewrite after old corrections can be expensive; an anchored,
  bounded replacement strategy must be validated before activation.
- Recorder data is reproducible from accepted source observations; it must
  not be treated as an independent utility record.
- Rebuild and repair operations must be tested with the exact installed
  Home Assistant Recorder APIs. A backup remains prudent but is not the
  required recovery mechanism for integration-owned statistics.

## References

- `docs/adr/0000-record-architecture-decisions.md`
- `docs/dev/HISTORICAL_STATISTICS.md`
- `custom_components/energy_usage/history.py`
- `custom_components/energy_usage/history_fetch.py`
- `custom_components/energy_usage/history_reconcile.py`
- [Home Assistant Recorder statistics API changes](https://developers.home-assistant.io/blog/2025/10/16/recorder-statistics-api-changes/)

- [Green Button Alliance ESPI unit codes](https://www.greenbuttonalliance.org/usage-data)
- [Home Assistant long-term statistics](https://www.home-assistant.io/docs/configuration/long-term-statistics/)
