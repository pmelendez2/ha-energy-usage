<!-- SPDX-License-Identifier: MIT -->
# Energy Usage — Quick Start

**Audience:** Home Assistant users

**Purpose:** Install and display electricity and gas usage simply.

**Status:** Published <!-- current-version:ha-energy-usage -->v0.1.5<!-- /current-version:ha-energy-usage --> quick start

**Release:** 0.1.5

**Last Updated:** 2026-11-24

**First:** Install Energy Ingest and its MariaDB database, register physical
electricity and/or gas meters, and start its authenticated API. You need Home
Assistant with Recorder enabled. Follow the concrete [prerequisites and token
copy instructions](INSTALLATION.md#1-prerequisites) before installing this
integration; its database is not created by HACS.

## 1. Install from HACS

1. In **HACS**, search the default catalog for **Energy Usage**.
2. Open **Energy Usage** and download the latest compatible published
   release (v0.1.5 at this documentation update).
3. Restart Home Assistant. A custom repository is not required.

Install **Energy Ingest <!-- current-version:energy-ingest -->v0.1.10<!-- /current-version:energy-ingest -->** first. The earlier v0.1.9
interoperability tests remain recorded for historical reference.

## 2. Connect your Energy Ingest server

Open **Settings → Devices & services → Add integration → Energy Usage**.
Enter the API base URL (for example, `http://ENERGY-INGEST-HOST:8080`).
On your Energy Ingest host, display the generated token by following
[Copy the bearer token](INSTALLATION.md#copy-the-bearer-token), then paste
only its value into the **API bearer token** field. Home Assistant should discover
your electricity and gas meters. The URL must be reachable from the Home
Assistant container; `localhost` usually refers to the wrong container.

### Optional: enable scheduled synchronization

Scheduled synchronization is **disabled by default**. To opt in, open
**Settings → Devices & services → Integrations → Energy Usage → Configure**,
enable **Automatic synchronization**, choose every **6**, **12**, or **24 hours**
(default), or **7 days**, and optionally enable **Synchronize on startup**.
Startup synchronization is off by default. The interval is not a fixed
clock time. See [INSTALLATION.md](INSTALLATION.md#choose-whether-to-enable-automatic-synchronization)
for the complete instructions. The Utility Card's confirmed-import
synchronization works independently of this optional schedule.

## 3. Import or synchronize existing history

For new Green Button XML downloads, follow
[step 5](#5-import-new-utility-xml-files).
You do not need to pre-import XML into Energy Ingest.

If Energy Ingest already contains accepted observations and Recorder has no
statistics for the meter, the initial import button remains available:

Open each device in **Settings → Devices & services → Energy Usage**.
Press **Import complete history (once)** for electricity and for gas.

The button checks the resolved stream, discovers its complete local date
range, and queues only actual readings. No meter IDs, dates, scripts, or
YAML are needed. Existing Recorder statistics are never overwritten.

**Important:** The initial importer can write each series only once and
supports at most 441 calendar days. It cannot append new observations or
correct older ones. If data already exists, stop; do not delete it. If the
import fails, see [Troubleshooting](docs/TROUBLESHOOTING.md).

## 4. Select the statistics in the Energy Dashboard

Under **Settings → Dashboards → Energy**, choose **Electric usage** for
electricity imported from the grid and **Gas usage** for gas consumption.
Keep costs disabled. Open a month that contains imported observations;
the present month may be empty when the utility data ends earlier.

## 5. Import new utility XML files

Use the recommended Energy Ingest v0.1.10 backend. If usage data
is already imported, you do not need to upload the same XML again.

### Register the Utility Card resource

1. Open **Settings → Dashboards → Resources**.
2. Select **Add resource** and enter this URL:

   ```text
   /energy-usage/energy-usage-utility-card.js
   ```

3. Select **JavaScript module**, then save. Do not enter card YAML in
   Resources; the resource URL must end in `.js`.

### Add the Utility Card to a dashboard

1. Open your dashboard and select **Edit dashboard → Add card → Manual**.
2. Enter the card configuration:

   ```yaml
   type: custom:energy-usage-utility-card
   ```

3. Save the card.

### Configure the utility download website

1. In **Edit dashboard**, edit the **Energy Usage Utility Card**.
2. Under **Download websites for registered utilities**, enter the utility's
   HTTP or HTTPS download website (for example, `http://www.sdge.com`).
3. Save and confirm **Download data from SDG&E**, or the corresponding
   utility name, appears above **Choose Files**.

You may also configure how many reading resources are shown per page.
With multiple registered utility companies, select the appropriate
**Utility Company** in the card before importing XML.

The card does not require a utility website URL to load. If configured,
the link opens that website in a separate browser tab. The URL is not
the Energy Ingest API address; configure that connection through the
Energy Usage integration instead. A failed utility-company request
shows a diagnostic status and does not enable imports. The card
retrieves registered utility companies from Energy Ingest and displays their
names. When only one company is registered, its dropdown is hidden and it
is selected automatically. With multiple companies, select the appropriate
Utility Company for the XML batch. Sign in
at the utility website yourself, download actual Green Button XML, choose
the electricity and/or gas files, then select **Import XML files**.
Review the association status for each returned reading resource. Existing
backend-confirmed meter mappings are retained and synchronize automatically
after the complete XML batch is imported. For unresolved resources, select
the correct physical meter and choose **Confirm physical meters**; Recorder
synchronization then begins automatically. Inspect Recorder verification
separately from import acceptance.
No utility passwords or API tokens belong in card configuration.

For file selection, imports, meter association, recovery and safe
retries, follow [the full installation procedure](INSTALLATION.md#download-and-import-xml).
Do not interpret an accepted XML file as proof that Recorder
synchronization has completed.

## 6. Add Energy Usage Explorer (optional)

Under **Settings → Dashboards → Resources**, add this JavaScript module:

```text
/energy-usage/energy-usage-explorer.js
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
