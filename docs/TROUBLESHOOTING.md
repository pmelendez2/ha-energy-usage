<!-- SPDX-License-Identifier: MIT -->
# Energy Usage Troubleshooting

**Audience:** Home Assistant users and administrators

**Purpose:** Resolve common installation and history-import errors

**Status:** Proposed for 0.1.1

**Release:** 0.1.1

**Last Updated:** 2026-10-26

| Symptom | What to do | How to verify or correct it |
| --- | --- | --- |
| HACS says repository already exists | Use the existing entry. | In **HACS**, search for **Energy Usage**, open it and download it. Do not add the repository again. |
| Energy Usage is absent from **Add integration** | Complete installation and restart. | In HACS, open **Energy Usage → Download**. Restart Home Assistant, refresh the browser, and open **Settings → Devices & services → Add integration**. |
| Cannot connect to Energy Ingest | Verify the API is running and reachable. | On the Energy Ingest host, run `"$HOME/energy-ingest-prod/scripts/verify-prod.sh"`. In Home Assistant's **API URL** field, enter the address of that host (for example `http://piha:8080`), not `127.0.0.1` when HA runs in a separate container. |
| API reports unauthorized / token not found | Retrieve the generated Home Assistant token. | Follow [Copy the bearer token](../INSTALLATION.md#copy-the-bearer-token). Paste the `ei_...` value into the integration's **API bearer token** field; do not prepend `Bearer`. Do not generate an arbitrary replacement. |
| No electricity or gas meters appear | Check meter registration. | On the Energy Ingest host, run `"$HOME/energy-ingest-prod/scripts/meter-prod.sh" list`. Complete meter creation and associations in Energy Ingest if none are listed. |
| No actual usage is available | Confirm utility files were imported. | Run `"$HOME/energy-ingest-prod/scripts/analyze-prod-data.sh"`. Check resource count and coverage; import actual Green Button files into Energy Ingest if coverage is missing. |
| Import reports unresolved history | Review source coverage or overlaps. | Run `"$HOME/energy-ingest-prod/scripts/analyze-prod-data.sh" --details`. Investigate conflicting source data in Energy Ingest before retrying; do not fabricate missing observations. |
| Import says history already exists | Inspect existing Recorder statistics. | In Home Assistant open **Developer tools → Statistics** and locate `energy_usage:electricity_meter_<ID>` or `energy_usage:gas_meter_<ID>`. If it reports **No issue** and graphs appear, the initial import already ran. Do not delete it or retry. |
| Button Activity only says “Pressed” | Check the meter's **Historical import status** diagnostic sensor. | **Imported** means Recorder contains history; **Importing** means persistence has not been confirmed; **Failed** means the last attempt failed without recorded history. Check the `last_attempt` and `last_error` sensor attributes to distinguish a failed repeat press from previously imported history. Status refreshes approximately every 30 seconds. |
| A button was pressed but success or failure is unclear | Open the Electric or Gas device's **Diagnostic** section. | **Historical import status** reports persisted data. **Last import attempt** reports the latest in-session operation; **Last import error** explains a failure. A failed repeat press can coexist with previously **Imported** data. The last-attempt details reset when Home Assistant restarts. |
| Import says the earlier request is still unconfirmed | Do not queue another import yet. | Check **Developer tools → Statistics** and the Recorder logs. If the import never persisted, restart Home Assistant to clear any outstanding in-process Recorder jobs. Confirm the statistic still has no rows before pressing the import button again. Never restart solely because the UI is slow. |
| Import exceeds 441 days | Stop at the current full-import limit. | Verify coverage with `analyze-prod-data.sh`. The initial importer cannot safely import that complete span; do not shorten it merely to make the first import succeed. |
| Import action says “Unknown error” but graphs exist | Determine whether data was already imported. | Open **Developer tools → Statistics** and inspect both series. A second v0.1.0 initial import returns an error when history already exists. |
| Energy Dashboard shows nothing today | Choose a period with imported data. | In the Energy Dashboard date picker, select a month within the coverage reported by `analyze-prod-data.sh`. Confirm **Settings → Dashboards → Energy** uses the correct electricity and gas statistics. |
| Gas is displayed in kWh | Check the original statistic unit. | In **Developer tools → Statistics**, verify that the gas series is in `thm`. Home Assistant can convert gas energy to kWh for display. |
| Explorer reports an unknown card | Check the JavaScript resource. | Under **Settings → Dashboards → Resources**, add `/energy_usage/energy-usage-explorer.js?v=0.1.1` as a **JavaScript module**, save, and refresh. Match the query version to the installed integration. |
| Gas has no hourly graph | Use its actual daily cadence. | Choose daily or monthly gas views. SDG&E gas observations are daily; no hourly samples are generated. |

Commands above use the standard Energy Ingest production bundle path. If
installed elsewhere, adjust the prefix. For Home Assistant logs, use
**Settings → System → Logs** when available, or your deployment's container
or service logs. Never share API tokens, original utility XML, or screenshots
containing credentials.
