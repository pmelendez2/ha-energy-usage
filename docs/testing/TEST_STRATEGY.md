<!-- SPDX-License-Identifier: MIT -->
# Test Strategy

> **Audience:** Maintainers and contributors
> **Purpose:** Test Strategy reference for Energy Usage.
> **Status:** Current documentation baseline
> **Release:** 0.1.0
> **Last Updated:** 2026-10-23

The Home Assistant integration will use repeatable automated and manual tests.

Testing includes:

- config flow;
- integration setup;
- unload/reload;
- connection to the ingestion service;
- historical statistics;
- electricity;
- gas;
- Energy Dashboard compatibility;
- duplicate/re-import behavior;
- diagnostics;
- localization;
- startup and recovery behavior;
- compatibility with supported Home Assistant releases.

Tests must run locally and in CI where practical.

Version-specific environments, evidence, and unsupported configurations
are recorded in [Tested Environments](TESTED_ENVIRONMENTS.md).
