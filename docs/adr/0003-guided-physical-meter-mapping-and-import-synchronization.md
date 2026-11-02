<!-- SPDX-License-Identifier: MIT -->

# 0003. Guided physical meter mapping and import synchronization

**Audience:** Maintainers and contributors

**Purpose:** Record the meter-selection and synchronization ordering contract
for guided Green Button uploads.

**Status:** Accepted

**Release:** 0.1.2

**Last Updated:** 2026-10-30

* Status: Accepted
* Date: 2026-10-30

## Context

<a href="0001-historical-utility-usage-recorder-synchronization.md">ADR-0001</a> establishes Home Assistant Recorder as a derived statistics store.
<a href="0002-utility-data-acquisition-and-synchronization.md">ADR-0002</a> establishes authenticated manual Green Button upload through Energy
Ingest and separately reported import and Recorder outcomes. However, a
successful import can introduce canonical meter-reading resources (for example, internal resource IDs
`13` and `14`, which are not physical meter numbers) that are
not yet attached to a physical meter. Synchronizing Recorder immediately
may therefore omit newly accepted observations without an import error.

Energy Ingest <a href="https://github.com/pmelendez2/energy-ingest/blob/main/docs/adr/0032-import-resource-identity-and-physical-meter-association.md">ADR-0032</a> (accepted) defines import-scoped canonical resource
identities and authoritative physical-meter association. Home Assistant
needs a guided, retryable workflow that consumes that contract without
independently deciding resource identity or canonical usage.

## Decision

### Meter configuration and selection

1. During integration setup and through options, the integration discovers
   physical meters using Energy Ingest's authenticated API and presents their
   authoritative identity and commodity to the user.
2. Existing configured meters and their persistent backend associations are
   preserved. The integration must not create duplicate meters or silently
   replace a physical-meter identity.
3. If meter creation is supported, it occurs through an explicit Energy
   Ingest operation with validated identity, user confirmation, and
   idempotent handling. The integration never writes Energy Ingest tables.
4. A previously confirmed, unambiguous persistent mapping may be reused.
   Unknown, ambiguous, or conflicting resource identities require user
   confirmation; commodity or candidate count alone never selects a meter.
5. Energy Ingest remains authoritative for validating and persisting the
   association. Home Assistant stores only configuration needed to resume
   the workflow, not an independent competing source of meter identity.

### Guided import sequence

1. The user selects an authorized acquisition source and uploads genuine
   Green Button XML through the authenticated Home Assistant upload path
   established by <a href="0002-utility-data-acquisition-and-synchronization.md">ADR-0002</a>.
2. After successful canonical import, the integration reads the canonical
   resource identities returned for that document, including when the same XML is re-imported with no new observations.
3. For each resource, it recognizes an existing association, reuses an
   explicitly confirmed persistent mapping, or requests confirmation.
4. It submits required associations to the authenticated Energy Ingest API
   and verifies their outcomes before treating affected meter history as
   ready for Recorder synchronization.
5. It synchronizes affected physical meters through the established
   correction-safe Recorder reconciliation path, then reports the verified
   persistence result separately from import and association outcomes.
6. A resource that remains unresolved or conflicting is not silently
   attached. The UI reports that accepted observations may not yet be
   represented in Recorder for the affected meter.

### Failures, retries, and presentation

1. An accepted Energy Ingest import remains accepted if association or
   Recorder synchronization subsequently fails. The integration reports
   the failed stage accurately and offers retry without fabricating data.
2. Repeated uploads and retries are idempotent. Recorder synchronization
   must reconcile accepted corrections and newly associated history rather
   than assuming only newly accepted observations matter.
3. The interface distinguishes imported, unchanged, associated, unresolved,
   and Recorder-verified results; no single success indicator conflates them.
4. Long per-resource or per-observation reports use a bounded, scrollable
   presentation with a user-configurable display limit. Presentation limits
   do not truncate canonical import or reconciliation work.
5. The integration does not collect utility login credentials, expose the
   Energy Ingest bearer token to the browser, or access MariaDB directly.

## Consequences

- The upload workflow must defer or scope Recorder synchronization until
  resource association has been verified; partial completion remains
  visible and retryable.
- Setup/options and upload interfaces require explicit meter selection and
  ambiguity handling, including keyboard-accessible confirmation states.
- Tests must cover first-time mapping, re-import, multiple meters of the same
  commodity, conflicting associations, API outages, Recorder failures,
  corrections, and repeated synchronization.
- The Energy Dashboard remains a derived view of actual validated
  electricity and natural-gas consumption. Missing intervals are not filled
  or estimated, and billing and rates remain out of scope.

## Alternatives considered

- **Synchronize immediately after import:** Rejected because unassociated
  resources may be omitted without a canonical import failure.
- **Choose the only meter of the same commodity:** Rejected because that
  does not establish physical-meter identity.
- **Maintain independent mappings in Home Assistant:** Rejected because it
  would create a competing authority and risk divergence from Energy Ingest.

## Related decisions

- <a href="0001-historical-utility-usage-recorder-synchronization.md">ADR-0001</a>: Historical utility usage synchronization with Recorder
- <a href="0002-utility-data-acquisition-and-synchronization.md">ADR-0002</a>: Utility data acquisition and synchronization
- `energy_ingest` <a href="https://github.com/pmelendez2/energy-ingest/blob/main/docs/adr/0030-home-assistant-integration-and-distributed-deployment.md">ADR-0030</a> and <a href="https://github.com/pmelendez2/energy-ingest/blob/main/docs/adr/0031-canonical-usage-validation-and-cli-home-assistant-consistency.md">ADR-0031</a>
- `energy_ingest` accepted <a href="https://github.com/pmelendez2/energy-ingest/blob/main/docs/adr/0032-import-resource-identity-and-physical-meter-association.md">ADR-0032</a>
