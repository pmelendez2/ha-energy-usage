# Test Plan

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
8. Update the supported/tested versions in `README.md`.

## Exit criteria

A Home Assistant version must not be listed as tested until the defined
compatibility tests have completed successfully.
