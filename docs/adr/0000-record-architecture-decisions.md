<!-- SPDX-License-Identifier: MIT -->
# 0000. Record architecture decisions

> **Audience:** Maintainers and contributors
> **Purpose:** 0000. Record architecture decisions reference for Energy Usage.
> **Status:** Current documentation baseline
> **Release:** 0.1.0
> **Last Updated:** 2026-10-23

* Status: Accepted
* Date: 2026-09-29

## Context

This project includes architectural decisions involving Green Button / ESPI
parsing, provider acquisition, authentication, data normalization, revision
handling, persistence, security, deployment, and interfaces to downstream
systems.

These decisions affect correctness and long-term maintainability. Their intent
should remain understandable to maintainers who were not involved when the
decision was made.

## Decision

Architecturally significant decisions will be recorded as numbered Markdown
files in `docs/adr/`.

Each ADR will contain:

- Status
- Date
- Context
- Decision
- Consequences

Accepted ADRs will not be rewritten to reflect later architectural changes.

When an accepted decision changes, a new ADR will document the new decision
and supersede the previous ADR.

Routine implementation details do not require an ADR.

## Consequences

Architectural intent and tradeoffs remain visible to future maintainers.

Changes to significant architecture require consideration of whether a new ADR
is appropriate.

Maintaining ADRs adds a small documentation cost, but avoids requiring future
maintainers to reconstruct architectural reasoning from source code and commit
history.
