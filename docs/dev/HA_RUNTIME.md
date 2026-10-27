<!-- SPDX-License-Identifier: MIT -->
<!-- AI-assisted: ChatGPT / GPT-6; 2026-10-16. -->

# Home Assistant Development Runtime

**Audience:** Developers and maintainers

**Purpose:** Home Assistant Development Runtime reference for Energy Usage.

**Status:** Current documentation baseline

**Release:** 0.1.1

**Last Updated:** 2026-10-27

## Purpose

Test the `energy_usage` integration in an isolated Home Assistant
instance before installing it on the production host. This is for
integration developers, not a customer installation procedure.

## Official environment setup

Follow the maintained Home Assistant contributor instructions:

- [Set up a development environment](https://developers.home-assistant.io/docs/development_environment/)
- [Integration testing](https://developers.home-assistant.io/docs/creating_integration_tests_file_structure/)
- [Config flows](https://developers.home-assistant.io/docs/core/integration/config_flow/)

Use the supported Dev Container workflow described by Home Assistant
and a separate development configuration directory. Do not mount or
modify the production Home Assistant configuration, database, or secrets.

Copy or link `custom_components/energy_usage` into the development
configuration's `custom_components/energy_usage` directory. Configure
an isolated Energy Ingest test API reachable from that environment.
Keep its bearer token in development-only configuration and never
commit it. Container loopback addresses are container-specific.

## Runtime acceptance checks

- Home Assistant starts with no manifest or import errors.
- The Energy Usage config flow accepts valid API credentials.
- Invalid credentials produce reauthentication, not silent failures.
- Meter discovery creates the supported diagnostic and import-button
  entities; button presses never import automatically on setup.
- Reload and unload do not leak tasks or duplicate entities.
- Network failure and recovery work without restarting MariaDB.

The Python unit tests use substitutes; passing them does not satisfy
these runtime checks. Guarded first-time Recorder import is implemented;
incremental synchronization and revision-aware correction are not.

## Initial backend connectivity verified (2026-10-19)

Development Home Assistant Core 2026.10.1 connected to Energy Ingest
v0.1.4 at a LAN HTTP API, authenticated with a dedicated bearer token.
Two devices and two entities were discovered (Electric and Gas).
The initial connectivity check did not verify historical statistics.
Subsequent runtime evidence is recorded in
[Tested Environments](../testing/TESTED_ENVIRONMENTS.md).
Avoid recording bearer tokens, URLs containing credentials or private XML.
