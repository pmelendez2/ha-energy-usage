<!-- SPDX-License-Identifier: MIT -->

# API documentation ownership

> **Audience:** Developers and maintainers
> **Purpose:** API documentation ownership reference for Energy Usage.
> **Status:** Current documentation baseline
> **Release:** 0.1.0
> **Last Updated:** 2026-10-23

The Rust `energy_ingest` service is the source of truth for its HTTP API.
Generate an OpenAPI 3 specification from the Rust route and schema definitions
(or a schema whose drift is checked by API contract tests). Publish an
`openapi.json` release artifact, and provide an optional Swagger UI for
local development. Interactive documentation must not expose API tokens or
allow anonymous access to privileged endpoints.

`ha_energy_usage` consumes the documented API and tests the responses it
needs; it must not independently publish a contradictory server schema.
