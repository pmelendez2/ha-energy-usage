# HA-TC-0001: Energy Dashboard displays imported usage

## Objective

Verify that imported residential electricity and gas statistics can be used by
the Home Assistant Energy Dashboard.

## Preconditions

- Supported Home Assistant Container release.
- Integration installed and configured.
- Known test electricity and gas data available.

## Procedure

1. Load the Home Assistant integration.
2. Import known electricity statistics.
3. Import known gas statistics.
4. Configure the Energy Dashboard to use the resulting statistics.
5. Open the Energy Dashboard.

## Expected result

- Electricity usage is available to the Energy Dashboard.
- Gas usage is available to the Energy Dashboard.
- Units and timestamps are correct.
- Historical data is shown without duplicate consumption.
