<!-- SPDX-License-Identifier: MIT -->
# Test Plan

> **Audience:** Maintainers and contributors
> **Purpose:** Test Plan reference for Energy Usage.
> **Status:** Current documentation baseline
> **Release:** 0.1.0
> **Last Updated:** 2026-10-23

The recorded verification matrix and its evidence are maintained in
[Tested Environments](TESTED_ENVIRONMENTS.md).

## Development baseline

- Home Assistant Container
- Home Assistant Core 2026.9.4
- Home Assistant Frontend 20260826.7
- Ubuntu 26.04 host

## Release validation

For each Home Assistant release considered for support:

1. Run the automated test suite.
2. Run the Home Assistant compatibility test matrix.
3. Perform a Container-based smoke test when required.
4. Verify electricity statistics.
5. Verify gas statistics.
6. Verify Energy Dashboard behavior.
7. Record known compatibility issues.
8. Add the verified environment and its evidence to
   [Tested Environments](TESTED_ENVIRONMENTS.md).
9. Update any user-facing compatibility summary only after recording evidence.

## Exit criteria

A Home Assistant version must not be listed as tested until the defined
compatibility tests have completed successfully.
