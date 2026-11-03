<!-- SPDX-License-Identifier: MIT -->
# Energy Usage — Quick Start

**Audience:** Home Assistant users

**Purpose:** Install and display electricity and gas usage simply.

**Status:** Published v0.1.2; utility upload preview in development

**Release:** 0.1.2

**Last Updated:** 2026-11-02

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

## 3. Import your complete history

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

## 5. Add Energy Usage Explorer (optional)

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

## Updating utility data (development preview)

The utility upload card is not included in the published v0.1.2 release.
For development validation, add `/energy-usage/energy-usage-utility-card.js`
as a JavaScript module under **Settings → Dashboards → Resources**.
Add **Custom: Energy Usage Utility Card** to a development dashboard.
Use the visual card editor to enter the utility's HTTPS download website
and optionally set the number of resources shown per page.
The preferred acquisition source ID is optional. If your Home Assistant
version does not show the visual editor, use **Show code editor**:

```yaml
type: custom:energy-usage-utility-card
# Optional: use the actual HTTPS utility download page.
# utility_url: https://your-utility.example/
# source_id is optional; choose a utility company in the card.
```

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

## Selecting utility XML files (development preview)

The utility dashboard card offers **Choose Files** and **Choose Folder**.
You can use either or both; selections are combined, and repeated files
are not added twice. Your browser asks permission to read the selected files; the
integration cannot set or remember your computer's Downloads directory.
Review the discovered XML files. Files are checked by default;
**Select all** is useful after unchecking some files, while **Clear
files** removes all listed filenames and resets the selection.
The **Import XML files** button remains disabled until a utility
company loads successfully and at least one file is checked. Only `.xml` files are shown.

The card requires a utility company from the backend catalog.
A batch must contain only XML files from that source; do not mix sources.
For unresolved resources, Energy Ingest supplies the canonical electricity
or natural-gas commodity. The card displays this usage type and offers only
compatible physical meters. Internal resource IDs are not the user-facing
choice. If commodity metadata is unavailable, the card blocks association
until a compatible Energy Ingest version is installed; filenames are never
used to guess the commodity.
Uploads require a Home Assistant administrator account. If canonical import
succeeds but a later step fails, pending resource IDs survive Home Assistant
restart in its protected storage. Reopen the card to resume without the XML;
if interrupted before pending IDs were saved, reimporting the same XML is
idempotent. Confirm mappings and use **Retry association and Recorder
synchronization** after an association or Recorder failure. The retry control
appears only when an earlier attempt needs attention. On reopening the card,
confirmed pending resources resume synchronization automatically. A progress
message identifies active synchronization and a completion message identifies
verified physical meters. The card never saves
the XML contents, utility credentials, or API token.

The card displays a separate result for each XML file. It explains whether
the file was previously imported, whether usage readings were added or
updated, whether existing readings needed no changes, or whether no usage
readings were processed. Files that have already been imported are clearly
identified, so you know that no further action is necessary.

After the files are processed, the card separately reports whether Home
Assistant history was synchronized successfully. A successful XML import
alone does not establish that Home Assistant history was updated.

Missing usage is never estimated, and billing or rates are out of scope.
