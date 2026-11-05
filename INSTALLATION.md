<!-- SPDX-License-Identifier: MIT -->
# Install and configure Energy Usage for Home Assistant

**Start here:** This guide covers the upcoming v0.1.5 installation,
including guided initial import and advanced validation procedures.

**Audience:** Users and administrators

**Purpose:** Guide first-time installation and usage-history import.

**Status:** v0.1.5 release preparation

**Release:** 0.1.5

**Last Updated:** 2026-11-04

This guide installs **Energy Usage** as a Home Assistant **custom integration**,
imports electricity and gas usage through the Utility Card, configures the
built-in Energy Dashboard, and optionally adds the Explorer card.

**Release scope:** v0.1.5 includes guided utility data import.
Energy Ingest 0.1.9 is required.
The utility upload card is included in Energy Usage 0.1.5.
Default HACS catalog inclusion is a separate approval process.

## 1. Prerequisites

1. **Install Energy Ingest and its MariaDB database first.** Follow the
   [Energy Ingest deployment instructions](https://github.com/pmelendez2/energy-ingest)
   for your host. The Energy Usage integration does not create that database.
2. **Register your physical electricity and/or natural gas meters** in
   Energy Ingest. The Utility Card imports actual Green Button XML after
   setup; an empty initial usage database is acceptable.
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

The verification should pass, and the meter list should show your physical
electricity and/or gas meters. Before your first XML upload, zero resources
and no usage coverage are expected. After importing XML through the Utility
Card, rerun the analysis to inspect resource associations, hourly electricity
or daily gas coverage, and any overlapping-source differences.
These commands assume the standard production bundle under
`$HOME/energy-ingest-prod`; adjust the installation directory if different.

### Copy the bearer token

The Energy Ingest production installer stores the **Home Assistant-specific
API token** in an owner-readable secret file. For the standard production bundle, the token file is:

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
https://github.com/pmelendez2/ha-energy-usage
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
5. Submit. Review the physical meter IDs, commodities, and names discovered
   from Energy Ingest. Confirm only when they match the intended physical
   meters. This confirmation does not attach XML resources to meters; guided
   import requests separate confirmation for unresolved resources.

If authentication fails after an Energy Ingest reinstall or token rotation,
reauthenticate / reconfigure the integration with the **new** token before
attempting historical imports. Do not delete Recorder data to fix API auth.

### Choose whether to enable automatic synchronization

**Automatic scheduled synchronization is off by default in v0.1.5.**
After adding the integration, opt in if you want Energy Usage to periodically
reconcile accepted electricity and natural gas observations with Home Assistant
Recorder. The integration does not turn on its schedule automatically.

1. Open **Settings → Devices & services → Integrations → Energy Usage**.
2. Open the integration's **Configure** options (the menu location varies by
   Home Assistant version).
3. Turn on **Automatic synchronization** to opt in.
4. Choose a **Synchronization interval**: every **6 hours**, **12 hours**,
   **24 hours** (the default selection), or **7 days**.
5. Optionally turn on **Synchronize on startup** if you also want a run after
   Home Assistant starts. This option is off by default.
6. Submit/save the options. Return here to change the interval or turn off
   automatic synchronization at any time.

The interval is a **frequency**, not a fixed clock time. Leaving automatic
synchronization disabled does not prevent manually initiated imports or the
Utility Card's confirmed-import synchronization workflow described below.
Automatic synchronization uses only accepted utility observations; missing
readings remain missing and existing corrections are reconciled safely.

## 4. Check the source and meters

Run the [read-only production checks](#confirm-energy-ingest-data-is-ready)
and confirm the expected physical meters appear. If XML has already been
imported, the analysis script's `--details` option shows diagnostic resource
IDs and overlapping values:

```bash
"$HOME/energy-ingest-prod/scripts/analyze-prod-data.sh" --details
```

Energy Usage validates accepted API readings before Recorder synchronization.
Unresolved source data is not silently imported into Home Assistant. Users
do not need to construct API calls or reveal their token for this check.

Electricity source cadence is normally **hourly**. Natural gas source cadence
is normally **daily**. A reported zero reading is actual data. An absent
reading is missing data and must **not** be replaced with zero.

## 5. Add the Utility Card and import Green Button XML

The Utility Card ships with Energy Usage v0.1.5. It is not automatically
added to the Energy Dashboard or the Home Assistant card picker. You must
register its JavaScript resource and add a Manual card.

### Register the JavaScript resource

1. Open **Settings → Dashboards → Resources** (the three-dot menu under
   Dashboards on versions that place Resources there).
2. Select **Add resource** and enter this URL:

   ```text
   /energy-usage/energy-usage-utility-card.js
   ```

3. Select **JavaScript module** and save. Do not enter `type: custom:...`
   in Resources; that belongs in the dashboard card editor.

### Add the dashboard card

1. Open the dashboard you want to use and select **Edit dashboard**.
2. Select **Add card → Manual** (or **Show code editor**) and enter:

   ```yaml
   type: custom:energy-usage-utility-card
   ```

3. Save the card.

### Configure the download website

1. Select **Edit dashboard** and edit the **Energy Usage Utility Card**.
2. Under **Download websites for registered utilities**, enter the utility's
   HTTP or HTTPS website address (for example, `http://www.sdge.com` for
   SDG&E). Some sites automatically redirect HTTP visitors to HTTPS.
3. Save the card. Confirm **Download data from SDG&E** (or your utility's
   name) appears above **Choose Files**.

The website is optional. Never put utility credentials or API tokens in
card configuration.

If the card says **Custom element doesn't exist**, check that the resource
URL returns HTTP 200, that its type is JavaScript module, and that Home
Assistant has restarted since the integration was installed. Refresh the
browser cache after upgrading; do not append a version query to the URL.

### Download and import XML

1. Sign in at your utility's website and download its actual **Green Button
   XML** usage files for electricity and/or natural gas.
2. Open the Utility Card. With multiple registered utilities, select the
   correct **Utility Company**. With only one registered company, the card
   selects it automatically and hides the dropdown.
3. Use **Choose Files** or **Choose Folder**. Check the XML filenames you
   want to import. **Select all** checks the listed files; **Clear files**
   removes the filenames and selections. Do not mix utilities in one batch.
4. Select **Import XML files**. Review the outcome for each file; successful
   XML acceptance alone does not mean Recorder synchronization has finished.
5. Previously confirmed physical-meter associations are reused. For any
   unresolved reading resources, choose the correct compatible physical
   meter and select **Confirm physical meters**. Synchronization begins
   automatically after confirmation; no separate sync confirmation is needed.
6. Wait for the progress and completion messages, then verify Recorder
   statistics in step 6. If an operation fails, use the retry control shown
   by the card. Pending associations can be recovered after a restart.

Only actual utility-provided readings are imported; gaps remain missing.
The card requires an administrator account for XML upload.

### Alternative: initial history import from existing Energy Ingest data

Use this alternative only when usage observations were already imported into
Energy Ingest and a meter has no Home Assistant Recorder statistics yet.
It is not the XML upload workflow and must not be used to overwrite history.

**Important — the alternative initial importer only:** This action refuses
to append to or replace existing statistics. Do not import a short sample
period first or delete good history to repeat the initial import. The Utility
Card's normal synchronization uses the separate correction-safe workflow.

#### Initial import button

Open **Settings → Devices & services → Energy Usage**, select each physical
meter device, and press **Import complete history (once)**. The button
automatically verifies accepted source readings, discovers their actual
date range, and queues the initial Recorder statistics. It will report
existing history as a validation error rather than overwriting it. No IDs,
dates, service YAML, or separate API calls are needed.

#### Optional manual import action

Open **Tools → Actions** (wording depends on your
Home Assistant version). Select the action
`energy_usage.import_historical_usage`. Provide the fields below.

##### Electricity example

```yaml
action: energy_usage.import_historical_usage
data:
  meter_id: 1
  start_date: "2025-09-07"
  end_date: "2026-10-06"
  confirm_initial_import: true
```

##### Natural gas example

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

Open **Tools → Statistics** and find your imported
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

## 8. Add Energy Usage Explorer (optional)

Explorer is bundled with the integration; no separate JavaScript download or
copy into `/config/www` is required.

1. Under **Settings → Dashboards → Resources**, add
   `/energy-usage/energy-usage-explorer.js` as a **JavaScript module**.
2. Edit a dashboard, choose **Add card → Manual**, and enter:

   ```yaml
   type: custom:energy-usage-explorer
   ```

   Explorer automatically discovers available `energy_usage:` statistics from
   Home Assistant Recorder, including electricity-only or gas-only setups and
   multiple physical meters. Alternatively, specify one or both statistic IDs
   explicitly (substitute IDs shown under **Tools → Statistics**):

   ```yaml
   type: custom:energy-usage-explorer
   electricity_statistic: energy_usage:electricity_meter_7
   gas_statistic: energy_usage:gas_meter_12
   ```

   The initial date range is the most recent 30 local calendar days, using
   Home Assistant's configured timezone. Select **Use latest available** to
   locate recorded observations; dates without readings remain empty.

3. Save and refresh. The resource URL should return HTTP 200. Verify hourly
   bars, line charts, date navigation, and selected-reading details.

Explorer displays actual electricity and gas usage without filling gaps.
If you previously registered the underscore-path Explorer resource, replace
it with the hyphenated URL above; the older URL is no longer served.

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
- The Utility Card reports completion for every imported XML batch and
  confirms synchronization of mapped physical meters.

## 10. Troubleshooting

| Symptom | Check |
| --- | --- |
| Cannot connect / token rejected | URL reachable **from Home Assistant**; current bearer token; reauthenticate after rotation |
| Import reports overlap / unresolved window | Check Energy Ingest resolved streams, local time zone, and compatible integration version; do not disable strict checks indiscriminately |
| Import reports statistics already exist | Initial-import-only mode; do not retry or overwrite an existing series |
| Gas missing in Energy Dashboard dropdown | Recorder unit should be `thm` with compatible energy metadata, not plain `therm` with an untyped unit class |
| Dashboard empty today | Select a date/month **within imported history** |
| Custom element not found | Check the corresponding `/energy-usage/energy-usage-utility-card.js` or `/energy-usage/energy-usage-explorer.js` URL for HTTP 200, use JavaScript module, then refresh the browser. |
| Gas hourly chart unavailable | Expected: source gas observations are daily; no hourly values are fabricated |
| Partial month labeled as month | Treat totals as **selected observations only**; inspect selection range and coverage |
| Unexpected zero readings | Compare accepted Energy Ingest values before assuming zeros were generated |

## 11. Important operational limits

During configuration-entry unload, scheduling stops and admitted operations
are drained before their shared runtime is discarded. An API failure must
not be interpreted as a successful synchronization; the next cycle may retry.
Recorder imports are asynchronous and success requires complete read-back
verification. Missing source periods are never synthesized. Billing dollars,
rates, credits, and solar sell-back monetary calculations remain out of scope.
