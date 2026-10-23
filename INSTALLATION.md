<!-- SPDX-License-Identifier: MIT -->
# Install and configure Energy Usage for Home Assistant

> **Audience:** Users and administrators
> **Purpose:** Install and configure Energy Usage for Home Assistant reference for Energy Usage.
> **Status:** Release candidate
> **Release:** 0.1.0
> **Last Updated:** 2026-10-23

This guide installs **Energy Usage** as a Home Assistant **custom integration**,
imports initial electricity and gas history, configures the built-in Energy
Dashboard, and optionally installs the Energy Usage Explorer custom card.

**Release:** 0.1.0 (release candidate; publication pending).
HACS custom-repository installation requires a published compatible release.
Default HACS catalog inclusion is a separate approval process.

## 1. Prerequisites

Before starting, confirm the following:

- Home Assistant is running, Recorder is enabled, and you know its **config**
  directory (inside the container this is typically `/config`).
- The separate **Energy Ingest** server has already imported and validated
  actual electricity and gas observations.
- You know the **Energy Ingest API address reachable from Home Assistant**,
  and have a Home Assistant-specific API bearer token. `127.0.0.1` inside a
  Home Assistant container is **not** the Energy Ingest host unless both share
  the same network namespace.
- You can discover the correct physical meter IDs using Energy Ingest meter
  inventory. Do **not** assume meter 1 / meter 2 on another installation.
- Home Assistant's **Settings → System → General → Time zone** matches the
  intended local reporting time zone.

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

### Option B: HACS custom repository (once released)

If HACS is installed and a public compatible repository is available, open
**HACS → ⋮ → Custom repositories**, enter the published GitHub repository URL,
select **Integration**, add it, then download **Energy Usage**. Restart Home
Assistant and refresh the browser. This is a **custom repository** workflow;
the integration is not claimed to be listed in HACS by default.

Official HACS documentation:
https://www.hacs.dev/docs/faq/custom_repositories/

## 3. Add Energy Usage to Home Assistant

1. In Home Assistant open **Settings → Devices & services → Add integration**.
2. Search for **Energy Usage**.
3. Enter the reachable **Energy Ingest API base URL**, such as
   `http://YOUR-ENERGY-INGEST-HOST:8080` (example only).
4. Enter the dedicated **API bearer token**. Never share it in support output.
5. Submit. Confirm the meter inventory is discovered and check that the
   electricity and gas physical meters are correctly identified.

If authentication fails after an Energy Ingest reinstall or token rotation,
reauthenticate / reconfigure the integration with the **new** token before
attempting historical imports. Do not delete Recorder data to fix API auth.

## 4. Validate the source history before importing

The initial import trusts Energy Ingest to resolve and validate canonical
meter intervals. Confirm each meter's stream has `resolved: true`, an expected
interval count, and zero issues. Use Energy Ingest's authenticated inspection
or administration tools; do not expose the token in screenshots.

Electricity source cadence is normally **hourly**. Natural gas source cadence
is normally **daily**. A reported zero reading is actual data. An absent
reading is missing data and must **not** be replaced with zero.

## 5. Import historical usage into Recorder

> **Important — initial import only:** The current action refuses to append to
> or replace an existing statistic series. Choose the **complete known history
> range before the first import**. Do not test with a short initial import and
> then expect to extend the same series with another action call.

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
3. Add the following resource URL:

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
