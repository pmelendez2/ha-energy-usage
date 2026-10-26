<!-- SPDX-License-Identifier: MIT -->
# Roadmap

> **Audience:** Maintainers and contributors
> **Purpose:** Roadmap reference for Energy Usage.
> **Status:** Current documentation baseline
> **Release:** 0.1.0
> **Last Updated:** 2026-10-23

## Implemented for release 0.1.0

- Home Assistant custom integration and configuration flow.
- Authenticated meter discovery and registration diagnostics.
- Explicit first-time import of hourly electricity and daily gas observations.
- Built-in Energy Dashboard long-term statistics integration.
- Bundled Energy Usage Explorer, including charts and point details.
- Isolated tests, source-package checks, and HACS validation workflow.

## Planned work

- Incremental synchronization and correction-safe revision handling.
- Broader Home Assistant release/platform compatibility evidence.
- Additional translation locales and expanded Explorer internationalization.
- HACS default-catalog review (separate from custom-repository install).

Missing utility-provided readings must stay missing; billing and solar
monetary reconciliation remain outside scope.
