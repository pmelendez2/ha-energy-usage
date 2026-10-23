<!-- SPDX-License-Identifier: MIT -->
# Energy Usage for Home Assistant

> **Audience:** Users and administrators
> **Purpose:** Energy Usage for Home Assistant reference for Energy Usage.
> **Status:** Release candidate
> **Release:** 0.1.0
> **Last Updated:** 2026-10-23

**Energy Usage** (`ha_energy_usage`) is a community-developed Home Assistant
custom integration that reads accepted electricity and natural gas consumption
from a separately installed **Energy Ingest** service. It can import utility
history into Home Assistant Recorder for the built-in Energy Dashboard and can
provide an optional **Energy Usage Explorer** dashboard card.

> **Release status:** Development / pre-release. The initial historical import
> and dashboard visualization have been validated in an isolated Home Assistant
> development instance. This document does **not** imply that this integration
> has been accepted into Home Assistant Core or the HACS default catalog.

## Features

- Discover supported physical electricity and natural gas meters through the
  authenticated Energy Ingest API.
- Import **actual, validated** historical consumption into Home Assistant
  long-term statistics, including hourly electricity and daily natural gas.
- Configure distinct electricity grid consumption and natural gas consumption
  in the built-in Home Assistant Energy Dashboard.
- Optionally install the **Energy Usage Explorer** dashboard card with typed
  start/end dates, monthly/daily/hourly selection, bar/line display, total and
  average usage, local-time labels, and click-to-inspect aggregates.
- Preserve genuine zero readings and leave missing observations missing; never
  interpolate, synthesize, or estimate utility consumption.
- Keep billing, rates, charges, credits, and solar monetary values out of scope.

## Architecture

```text
Utility Green Button XML → Energy Ingest → MariaDB
                                      ↓ authenticated API
                              Energy Usage integration
                                      ↓ initial import
                           Home Assistant Recorder
                                      ↓
                       Energy Dashboard / Usage Explorer
```

Energy Ingest is a separate prerequisite. This integration does **not**
download utility account data directly, manage Energy Ingest's database, or
install the Energy Ingest server.

## Requirements

- A running Home Assistant instance with long-term statistics / Recorder.
- A compatible, reachable **Energy Ingest** HTTP API.
- An Energy Ingest bearer token issued for Home Assistant.
- Actual accepted meter observations already loaded into Energy Ingest.
- Home Assistant's configured time zone matching the intended local reporting
  calendar when importing historical observations.

Initial runtime validation was performed with Home Assistant Container on
Ubuntu, using Home Assistant Core 2026.10.1 in development. Broader supported
version ranges and platforms require release validation.

## Get started

Follow **[INSTALLATION.md](INSTALLATION.md)** from start to finish for:

1. Provisioning and checking Energy Ingest API access.
2. Installing the custom integration (manual; HACS custom repository once a
   compatible public GitHub release is available).
3. Adding **Energy Usage** in **Settings → Devices & services**.
4. Importing electricity and gas history **once** into an empty Recorder
   statistic series.
5. Configuring electricity and gas separately in the Energy Dashboard.
6. Optionally installing **Energy Usage Explorer** as a Lovelace JavaScript
   resource and card.
7. Verifying values and diagnosing common failures.

## Current limitations

- **Historical import is initial-import-only.** It refuses to overwrite an
  existing statistic series. Incremental updates and correction-safe automatic
  synchronization are not yet available; do not advertise this as a continuous
  feed.
- **Gas observations are daily.** An hourly gas graph must not invent readings.
- Custom card controls and source compatibility must be tested against each
  supported Home Assistant release.
- The Energy Dashboard can express gas in kWh after converting the Recorder
  energy unit `thm`; Explorer labels it in familiar **therm** units.
- Accepted consumption data and a successful action call do not, alone, prove
  that every period was persisted correctly; inspect Recorder statistics.
- A partial selected calendar month must not be mistaken for an entire month's
  usage. Incomplete intervals require visible coverage information.

## Privacy and security

Keep credentials, personal utility XML, tokens, and customer-specific meter
identifiers out of commits, support screenshots, and issue reports. Use HTTPS
when the API is reachable over untrusted networks. Do not expose its token in
Lovelace JavaScript or browser-side resources; the Explorer reads Home Assistant
Recorder statistics using the authenticated Home Assistant session.

## Installation and releases

See [Installation and configuration](INSTALLATION.md) for user setup,
explicit initial import, Energy Dashboard, and the Explorer card.

Versioned releases are published on the
[GitHub Releases page](https://github.com/pmelendez2/ha_energy_usage/releases).
HACS custom-repository installation is distinct from default-catalog approval.

## Development and contributions

See [Contributing](CONTRIBUTING.md) for maintainer and test workflows.

## License

MIT; see [LICENSE](LICENSE).
