<!-- SPDX-License-Identifier: MIT -->
# Install and configure Energy Usage for Home Assistant

**Start here:** [Quick Start](QUICKSTART.md) is the concise installation
path for upcoming 0.1.1 improvements. This document retains the detailed
0.1.0 manual instructions and advanced validation procedures.

**Audience:** Users and administrators

**Purpose:** Guide first-time installation and usage-history import.

**Status:** Published 0.1.0; guided workflow proposed for 0.1.1

**Release:** 0.1.1

**Last Updated:** 2026-10-23

This guide installs **Energy Usage** as a Home Assistant **custom integration**,
imports initial electricity and gas history, configures the built-in Energy
Dashboard, and optionally installs the Energy Usage Explorer custom card.

**Published release:** 0.1.0 is available on GitHub Releases.
The guided import buttons are proposed for unreleased 0.1.1.
Default HACS catalog inclusion is a separate approval process.

## 1. Prerequisites

1. **Install Energy Ingest and its MariaDB database first.** Follow the
   [Energy Ingest deployment instructions](https://github.com/pmelendez2/energy_ingest)
   for your host. The Energy Usage integration does not create that database.
2. **Import actual electricity or natural gas observations into Energy
   Ingest** before setting up Energy Usage in Home Assistant. An empty
   database or newly registered meters alone are not enough.
3. **Start the Energy Ingest API** and confirm its production deployment
   passes verification. Record the API hostname and port reachable from Home
   Assistant. `127.0.0.1` inside Home Assistant ordinarily refers to the
   Home Assistant container, not the separate Energy Ingest container.
4. **Locate the generated Home Assistant-specific bearer token.** Use the
   steps below to display it privately and paste it into Home Assistant.
5. **Run Home Assistant with Recorder enabled**, an appropriately configured
   local time zone, and access to the API. For a manual installation you
   also need access to its configuration directory (usually `/config`).

### Confirm Energy Ingest data is ready

On the **Energy Ingest production host**, run these read-only checks:

```bash
"$HOME/energy-ingest-prod/scripts/verify-prod.sh"

"$HOME/energy-ingest-prod/scripts/meter-prod.sh" list

"$HOME/energy-ingest-prod/scripts/analyze-prod-data.sh"
```

The verification should pass; the meter list should show your electricity
and/or gas meter with associated resources. Data analysis should report
imported resources, hourly electricity or daily gas coverage, and any
overlapping-source differences. If the database is empty, import your utility
files using the Energy Ingest installation's import procedure first.
These commands assume the standard production bundle under
`$HOME/energy-ingest-prod`; adjust the installation directory if different.

### Copy the bearer token

The Energy Ingest production installer stores the **Home Assistant-specific
API token** in an owner-readable secret file. For the deployed production
bundle tested on `piha`, its exact path is:

```text
$HOME/energy-ingest-prod/deploy/docker-compose/prod-secrets/ha_energy_dev_api_token
```

Despite `dev` in the filename, this is the dedicated Home Assistant API
token created by that production installer. On the **Energy Ingest host**:

```bash
TOKEN_FILE="$HOME/energy-ingest-prod/deploy/docker-compose/"
TOKEN_FILE="${TOKEN_FILE}prod-secrets/ha_energy_dev_api_token"

if [[ -s "$TOKEN_FILE" ]]; then
    cat "$TOKEN_FILE"
else
    printf 'Home Assistant API token file not found\n' >&2
fi
```

Copy only the single token value displayed, beginning with `ei_`. In the
Home Assistant **Add integration → Energy Usage** dialog, paste it into
the **API bearer token** field; put the hostname and port into the
separate **API URL** field. Do not include `Bearer`, quotes, spaces, or the
filename. Close or clear the terminal after copying so the token does not
remain visible. Never paste it into chat, logs, dashboard cards, or Git.

If this file does not exist, use the credentials path documented by your
installed Energy Ingest production package; do not create a random substitute.

**Security:** Do not place bearer tokens in card YAML, source code, browser
JavaScript, or support logs. Keep the token in the integration configuration.

## 2. Install the integration

### Option A: Manual installation

Obtain a verified release of the repository. Copy its integration folder into
**your Home Assistant configuration** so the following file exists:

```text
/config/custom_components/energy_usage/manifest.json
```

On a host with a mounted Home Assistant configuration, the source may be copied
with a command like this **after replacing both paths**:

```bash
install -d /path/to/ha-config/custom_components
cp -a custom_components/energy_usage \
    /path/to/ha-config/custom_components/
```

Do not copy the entire Git repository into `custom_components/`. Do not apply
an example developer host path to production without checking the mount.
Restart the Home Assistant instance, then refresh the browser.

### Option B: HACS custom repository

The HACS custom repository is:

```text
https://github.com/pmelendez2/ha_energy_usage
```

1. Open **HACS** and its three-dot menu → **Custom repositories**.
2. Paste that exact URL, select category **Integration**, then **Add**.
3. Search HACS for **Energy Usage** and download the latest published release.
   If it is already listed, open it directly instead of adding it again.
4. Restart Home Assistant and refresh the browser.

This is a custom-repository installation until HACS's default catalog
accepts the integration.

Official HACS documentation:
https://www.hacs.dev/docs/faq/custom_repositories/

## 3. Add Energy Usage to Home Assistant

1. In Home Assistant open **Settings → Devices & services → Add integration**.
2. Search for **Energy Usage**.
3. Enter the reachable **Energy Ingest API base URL**, such as
   `http://YOUR-ENERGY-INGEST-HOST:8080` (example only).
4. On the Energy Ingest host, follow [Copy the bearer token](#copy-the-bearer-token).
   Paste the generated `ei_...` value into the **API bearer token** field.
   Do not include the `Bearer` prefix. Never share it in support output.
5. Submit. Confirm the meter inventory is discovered and check that the
   electricity and gas physical meters are correctly identified.

If authentication fails after an Energy Ingest reinstall or token rotation,
reauthenticate / reconfigure the integration with the **new** token before
attempting historical imports. Do not delete Recorder data to fix API auth.

## 4. Validate the source history before importing

For most users, the [read-only production data checks](#confirm-energy-ingest-data-is-ready)
from step 1 are sufficient preparation. Run `verify-prod.sh`, `meter-prod.sh
list`, and `analyze-prod-data.sh` on the Energy Ingest host and confirm that
the expected meters and coverage appear. If desired, the analysis script's
`--details` option shows diagnostic resource IDs and overlapping values:

```bash
"$HOME/energy-ingest-prod/scripts/analyze-prod-data.sh" --details
```

The guided **0.1.1 import button** then validates the actual accepted API
stream (`resolved: true`, `issues: []`) itself and refuses to import if the
source is unresolved. Users do not need to construct API calls or expose
their token for this validation. In **0.1.0**, the manual import action also
checks the accepted observations and refuses invalid or unresolved data.

Electricity source cadence is normally **hourly**. Natural gas source cadence
is normally **daily**. A reported zero reading is actual data. An absent
reading is missing data and must **not** be replaced with zero.

## 5. Import historical usage into Recorder

**Important — initial import only:** This release refuses to append to or
replace existing statistics. Do not import a short sample period first.
Do not delete good history in order to repeat the initial import.

### Recommended for 0.1.1 and later

Open **Settings → Devices & services → Energy Usage**, select each physical
meter device, and press **Import complete history (once)**. The button
automatically verifies accepted source readings, discovers their actual
date range, and queues the initial Recorder statistics. It will report
existing history as a validation error rather than overwriting it. No IDs,
dates, service YAML, or separate API calls are needed.

### Manual action for released 0.1.0

Open **Developer tools / Settings → Tools → Actions** (wording depends on your
Home Assistant version). Select the action
`energy_usage.import_historical_usage`. Provide the fields below.

### Electricity example

```yaml
action: energy_usage.import_historical_usage
data:
  meter_id: 1
  start_date: "2025-09-07"
  end_date: "2026-10-06"
  confirm_initial_import: true
```

### Natural gas example

```yaml
action: energy_usage.import_historical_usage
data:
  meter_id: 2
  start_date: "2025-09-07"
  end_date: "2026-10-06"
  confirm_initial_import: true
```

**These IDs and dates are examples from one tested dataset, not universal
values.** Use your actual discovered meter IDs and observed coverage.

Submit each action **only once**, wait for completion, then inspect the results.
If the action fails, check Home Assistant logs and statistics before retrying.
Do not delete an existing series or rerun an initial import casually.

## 6. Verify Recorder statistics

Open **Developer tools / Settings → Tools → Statistics** and find your imported
meter statistics. The default IDs follow the convention:

```text
energy_usage:electricity_meter_<ID>   (kWh)
energy_usage:gas_meter_<ID>           (thm)
```

`thm` is Home Assistant's canonical abbreviation for therms. Electricity
statistics should use unit `kWh`; natural gas statistics should use unit `thm`
and compatible energy metadata. The Gas statistic may display as kWh inside
the built-in Energy Dashboard after unit conversion; that does **not** mean
its underlying gas readings became electricity consumption.

Check that the statistics have **No issue** and that historical periods match
what Energy Ingest supplied. A gap is not necessarily a zero: cross-check
actual source observations if a period looks suspicious.

## 7. Configure the built-in Energy Dashboard

Open **Settings → Dashboards → Energy**, or edit the Energy Dashboard using its
configuration option. If the six-step wizard is shown, configure electricity
and gas in their **separate** sections.

### Electricity grid

- **Energy imported from grid:** select **Electric usage** for the matching
  `energy_usage:electricity_meter_<ID>` statistic.
- **Energy exported to grid:** leave empty, unless independent supported export
  data exists (not part of this integration's consumption scope).
- **Cost tracking:** **Do not track costs**.

### Gas consumption

- **Gas consumption:** select **Gas usage** for the matching
  `energy_usage:gas_meter_<ID>` statistic.
- **Gas flow rate:** leave empty.
- **Cost tracking:** **Do not track costs**.

The selectors may display **both** energy statistics. Be careful not to assign
**Gas usage** to the electricity grid, or **Electric usage** to gas. Save each
section. Skip unrelated solar, battery, or water steps if they do not apply.

Use the bottom date selector to select a **month or date range that actually
contains imported readings**. Selecting today's date when observations end
weeks earlier may show **No statistics found** and zero totals even when the
configuration is correct.

The Energy Dashboard is generated separately from custom Lovelace cards. It
will **not automatically display the Energy Usage Explorer custom card**.

Official Home Assistant references:
- https://www.home-assistant.io/docs/energy/
- https://www.home-assistant.io/docs/energy/gas/

## 8. Install Energy Usage Explorer


Energy Usage Explorer is included with the Energy Usage integration. It is installed with the integration, whether installed manually or through HACS.

No separate JavaScript download or manual copy into `/config/www` is required.

After installing Energy Usage and restarting Home Assistant:

1. Open **Settings → Dashboards**.
2. Open the three-dot menu and select **Resources**.
3. Add the resource URL matching your installed version. For released
   v0.1.0, use:

   `/energy_usage/energy-usage-explorer.js?v=0.1.0`

4. Select **JavaScript module** as the resource type.
5. Save the resource and reload the dashboard.

The JavaScript file is served directly by the Energy Usage integration from `custom_components/energy_usage/www/energy-usage-explorer.js`.

#### Verify the installation

Open `/energy_usage/energy-usage-explorer.js?v=0.1.0` on your Home Assistant server. It should return HTTP 200.

In the Explorer dashboard, verify that the hourly bar chart, line chart, date navigation, calculation controls, and selected-data-point details are available.

The Explorer uses actual electricity and natural gas consumption observations. Missing periods are not filled with estimated or invented readings.

## 9. Verify the result

Check all of the following before considering installation complete:

- Both physical meters are discovered with correct commodities.
- Electricity and gas history exist under distinct `energy_usage:` statistic
  IDs, with `kWh` and `thm` units respectively.
- The Energy Dashboard shows separate **Electricity** and **Gas** sections.
- October or another known historical sample reconciles with Energy Ingest.
- Real zero consumption remains zero; missing readings remain missing.
- DST transitions preserve actual local-date reporting without invented data.
- Explorer bar/line point selection opens a detail panel; its averages and
  coverage are interpreted in the context of selected observations.

## 10. Troubleshooting

| Symptom | Check |
| --- | --- |
| Cannot connect / token rejected | URL reachable **from Home Assistant**; current bearer token; reauthenticate after rotation |
| Import reports overlap / unresolved window | Check Energy Ingest resolved streams, local time zone, and compatible integration version; do not disable strict checks indiscriminately |
| Import reports statistics already exist | Initial-import-only mode; do not retry or overwrite an existing series |
| Gas missing in Energy Dashboard dropdown | Recorder unit should be `thm` with compatible energy metadata, not plain `therm` with an untyped unit class |
| Dashboard empty today | Select a date/month **within imported history** |
| Custom element not found | Confirm `/energy_usage/energy-usage-explorer.js?v=0.1.0` returns HTTP 200. Verify the resource type is JavaScript module, and reload the dashboard. |
| Gas hourly chart unavailable | Expected: source gas observations are daily; no hourly values are fabricated |
| Partial month labeled as month | Treat totals as **selected observations only**; inspect selection range and coverage |
| Unexpected zero readings | Compare accepted Energy Ingest values before assuming zeros were generated |

## 11. Important operational limits

This initial integration is **not** an automatic, revision-aware synchronization
service. New data and utility corrections will require a future supported
correction-safe sync design. Do not treat the initial importer as a recurring
update action. Billing dollars and solar sell-back monetary calculations are
out of scope.
