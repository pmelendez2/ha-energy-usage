<!-- SPDX-License-Identifier: MIT -->
# Upgrade Energy Usage for Home Assistant

**Audience:** Users and administrators

**Purpose:** Upgrade an existing Energy Usage installation without losing configuration or usage history.

**Status:** User documentation

**Release:** 0.1.5

**Last Updated:** 2026-11-04

This guide covers upgrading an existing installation to **v0.1.5**, once
that release is published. Do not install an unpublished development build.
For a first installation, use [INSTALLATION.md](../INSTALLATION.md).

## Before upgrading

1. Read the [v0.1.5 release notes](https://github.com/pmelendez2/ha-energy-usage/releases/tag/v0.1.5)
   after the release is published.
2. Confirm your Home Assistant configuration directory and the current version
   in `custom_components/energy_usage/manifest.json`.
3. Determine whether the integration is managed by HACS. If Energy Usage
   appears as a downloaded integration in HACS, use **HACS upgrade** below.
   Otherwise use **Manual upgrade**. Do not mix installation methods.
4. Keep the existing Home Assistant configuration, Recorder database, Energy
   Usage configuration entry, and Energy Ingest API credentials. **Do not remove
   and re-add the integration, rerun initial import, or delete statistics.**

## HACS upgrade

1. Open **HACS** and find the installed **Energy Usage** integration.
2. Open its entry and select the available **v0.1.5** update/download.
   If HACS does not show v0.1.5, confirm the custom repository is configured
   and that the release has been published; do not switch to manual installation
   over a HACS-managed copy.
3. Complete the download and restart Home Assistant using your installation's
   normal restart control.
4. Refresh the browser, then complete [Verify the upgrade](#verify-the-upgrade).

The project is not necessarily in the default HACS catalog; an existing custom
repository can still receive published releases.

## Manual upgrade

Obtain the **published v0.1.5 source archive** from the
[GitHub release](https://github.com/pmelendez2/ha-energy-usage/releases/tag/v0.1.5).
The archive must contain `custom_components/energy_usage/manifest.json` with
`"version": "0.1.5"`. Do not deploy files from an unreviewed development
branch. Use the release's published checksum if one is provided.

1. Extract the archive into a temporary directory on the host that can access
   Home Assistant's persistent configuration directory.
2. Confirm the extracted manifest reports `0.1.5`.
3. Copy **the contents of** `custom_components/energy_usage/` over the
   existing `<HA_CONFIG>/custom_components/energy_usage/` directory. Do not
   replace `<HA_CONFIG>` itself. Do not delete the existing configuration or
   Recorder database. Do not copy the entire Git repository into
   `custom_components/`.
4. In Home Assistant, select **Settings → System → Restart Home Assistant**.
   Use the normal application restart control. Do not force a container or
   service update merely to load changed integration files.
5. Refresh the browser and complete the verification below.

For Home Assistant Container installations, ensure the updated files are in
Home Assistant's persistent configuration volume before restarting. The
configuration path and container-management commands vary by installation.

## Verify the upgrade

1. Confirm the installed `custom_components/energy_usage/manifest.json`
   reports version `0.1.5` using the configuration file browser or your
   usual host file access method.
2. In Home Assistant, open **Settings → Devices & services → Energy Usage**.
   Confirm the existing configuration entry and electricity/gas meters remain.
3. Open **Settings → Tools → Statistics** and confirm the existing usage
   statistics are still present, without new errors.
4. Check the Energy Dashboard and Explorer for a historical date that already
   had observations before the upgrade. A missing period must remain missing.
5. Under **Settings → Dashboards → Resources**, confirm that the Explorer
   uses `/energy-usage/energy-usage-explorer.js` and the Utility Card uses
   `/energy-usage/energy-usage-utility-card.js`, both as JavaScript modules.
   Remove any old underscore-path Explorer resource and register the canonical
   URL. Dashboard cards themselves retain their `type: custom:...` YAML.
6. Open the Utility Card and verify any existing HTTP or HTTPS utility website
   is configured under **Download websites for registered utilities**.
7. If the integration fails to load, check Home Assistant logs before making
   any configuration or Recorder changes. Do not rerun the initial import to
   repair an upgrade failure.

The upgrade is complete when the installed version is 0.1.5 and the existing
configuration and historical usage remain available.

## v0.1.5 synchronization behavior

Automatic synchronization is **off by default**, including for existing
installations that have not explicitly opted in. In the Energy Usage
integration options, enable automatic synchronization to schedule recurring
checks. The default interval is 24 hours; other available intervals are
6 hours, 12 hours, and 7 days. Startup synchronization is separately
configurable and is disabled by default. Manual import and explicit
synchronization actions remain available.

## Utility reporting boundaries

The v0.1.5 gas import no longer rejects accepted daily readings solely
because their local reporting time differs from SDG&E's 23:59 convention.
Daily gas usage is associated with the reading's local calendar date. Utility
profiles whose timestamp represents a different reporting date require
separate canonical mapping verification before production use; no missing
usage is inferred or synthesized.

## Timezone handling in v0.1.5

Energy Usage does not configure or store a separate timezone. It uses the
current timezone selected in Home Assistant under **Settings → System →
General**. No `time_zone` entry is required in `configuration.yaml`.

Date ranges and daily natural-gas reporting dates are interpreted in that
Home Assistant timezone, including daylight-saving transitions. Existing
accepted utility observations are not shifted or synthesized.
