# Test Strategy

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
