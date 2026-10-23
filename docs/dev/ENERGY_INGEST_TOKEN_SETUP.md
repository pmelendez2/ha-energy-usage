<!-- SPDX-License-Identifier: MIT -->

# Automatic Home Assistant API token provisioning

> **Audience:** Developers and maintainers
> **Purpose:** Automatic Home Assistant API token provisioning reference for Energy Usage.
> **Status:** Current documentation baseline
> **Release:** 0.1.0
> **Last Updated:** 2026-10-23

**Status:** Backend implementation pending source verification.

**Repository:** `energy_ingest` (not `ha_energy_usage`).

## Required installer behavior

After database bootstrap and API client storage are available, the production
setup must detect whether a Home Assistant API client credential has already
been provisioned. On a new installation, it must generate a random 256-bit
opaque bearer token using the existing accepted ADR-0024 creation interface.
Store only its SHA-256 verifier in the database, and place the token itself
in a protected, owner-readable secret file outside tracked repository files.
The token must be shown to the operator only in a deliberate protected step.
Do not put the token in shell tracing, Compose command lines, URLs, GitHub
Actions output, general-purpose logs, or process arguments.

On repeated setup, preserve the existing token without replacement. Allow
explicit regeneration through an authenticated administrative action;
revoke the replaced verifier after confirming the new token works.

Use the same backend token-management implementation already used by
`energy-api-token`. Do not generate a separate incompatible credential or
invent a second verifier format.

## Integration testing

- Fresh setup creates exactly one authorized HA client.
- Repeated setup does not rotate or disclose the secret.
- Token authenticates at `GET /v1/meters`.
- Wrong or revoked tokens fail without logging secrets.
- File permissions and backup/restore lifecycle are verified.
- Partial setup or crash is safely recoverable.
- Token is available to the operator for HA setup.

**Integration blocker:** The current production `setup-prod.sh` and API-token
CLI source were not present in the available review archive. Do not modify the
production setup by guessing interfaces. Apply this in `energy_ingest` as soon
as those files are reviewed, then add the code and packaging to the production
release pipeline. This document is an implementation contract, not a claim
that automatic provisioning has been deployed.
