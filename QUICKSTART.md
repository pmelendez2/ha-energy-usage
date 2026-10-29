<!-- SPDX-License-Identifier: MIT -->
# Energy Usage — Quick Start

**Audience:** Home Assistant users

**Purpose:** Install and display electricity and gas usage simply.

**Status:** Proposed for 0.1.1; not included in released 0.1.0

**Release:** 0.1.2

**Last Updated:** 2026-10-26

**First:** Install Energy Ingest and its MariaDB database, import actual
electricity or gas usage, and start its authenticated API. You also need Home
Assistant with Recorder enabled. Follow the concrete [prerequisites and token
copy instructions](INSTALLATION.md#1-prerequisites) before installing this
integration; its database is not created by HACS.

## 1. Install from HACS

1. In HACS, open **Custom repositories** from the three-dot menu.
2. Add `https://github.com/pmelendez2/ha-energy-usage` as **Integration**.
   If it is already listed, do not add it again.
3. Open **Energy Usage**, download the latest compatible **published** release,
   and restart Home Assistant.

Energy Usage is a HACS custom repository until accepted into the default
catalog. Do not install an unreleased version from this guide.

## 2. Connect your Energy Ingest server

Open **Settings → Devices & services → Add integration → Energy Usage**.
Enter the API base URL (for example, `http://ENERGY-INGEST-HOST:8080`).
On your Energy Ingest host, display the generated token by following
[Copy the bearer token](INSTALLATION.md#copy-the-bearer-token), then paste
only its value into the **API bearer token** field. Home Assistant should discover
your electricity and gas meters. The URL must be reachable from the Home
Assistant container; `localhost` usually refers to the wrong container.

## 3. Import your complete history (0.1.1 and later)

Open each device in **Settings → Devices & services → Energy Usage**.
Press **Import complete history (once)** for electricity and for gas.

The button checks the resolved stream, discovers its complete local date
range, and queues only actual readings. No meter IDs, dates, scripts, or
YAML are needed. Existing Recorder statistics are never overwritten.

**Important:** The initial importer can write each series only once and
supports at most 441 calendar days. It cannot append new observations or
correct older ones. If data already exists, stop; do not delete it. If the
import fails, see [Troubleshooting](docs/TROUBLESHOOTING.md).

For released **0.1.0**, use the explicit one-time action documented in
[Installation](INSTALLATION.md); the import buttons are not in that version.

## 4. Select the statistics in the Energy Dashboard

Under **Settings → Dashboards → Energy**, choose **Electric usage** for
electricity imported from the grid and **Gas usage** for gas consumption.
Keep costs disabled. Open a month that contains imported observations;
the present month may be empty when the utility data ends earlier.

## 5. Add Energy Usage Explorer (optional)

Under **Settings → Dashboards → Resources**, add this JavaScript module:

```text
/energy_usage/energy-usage-explorer.js?v=0.1.1
```

In an editable dashboard, add a **Manual** card:

```yaml
type: custom:energy-usage-explorer
```

The Explorer displays observed electricity and gas history, bar and line
graphs, date navigation, totals, averages, and selected readings. Gas is
daily, not hourly. Missing periods remain missing; no billing is calculated.

For advanced installation, source validation, and manual troubleshooting,
see [Installation](INSTALLATION.md).
