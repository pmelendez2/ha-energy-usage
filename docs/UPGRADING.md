<!-- SPDX-License-Identifier: MIT -->
# Upgrade Energy Usage for Home Assistant

**Audience:** Users and administrators

**Purpose:** Upgrade an existing Energy Usage installation without losing configuration or usage history.

**Status:** User documentation

**Release:** 0.1.2

**Last Updated:** 2026-10-29

This guide covers upgrading an existing installation, including **0.1.0 to
0.1.2**. For a first installation, use [INSTALLATION.md](../INSTALLATION.md).

## Before upgrading

1. Read the [v0.1.2 release notes](https://github.com/pmelendez2/ha-energy-usage/releases/tag/v0.1.2).
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
2. Open its entry and select the available **v0.1.2** update/download.
   If HACS does not show v0.1.2, confirm the custom repository is configured
   and that the release is available; do not switch to manual installation
   over a HACS-managed copy.
3. Complete the download and restart Home Assistant using your installation's
   normal restart control.
4. Refresh the browser, then complete [Verify the upgrade](#verify-the-upgrade).

The project is not necessarily in the default HACS catalog; an existing custom
repository can still receive published releases.

## Manual upgrade

Obtain the **published v0.1.2 source archive** from the
[GitHub release](https://github.com/pmelendez2/ha-energy-usage/releases/tag/v0.1.2).
The archive must contain `custom_components/energy_usage/manifest.json` with
`"version": "0.1.2"`. Do not deploy files from an unreviewed development
branch. Use the release's published checksum if one is provided.

1. Extract the archive into a temporary directory on the host that can access
   Home Assistant's persistent configuration directory.
2. Confirm the extracted manifest reports `0.1.2`.
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
   reports version `0.1.2` using the configuration file browser or your
   usual host file access method.
2. In Home Assistant, open **Settings → Devices & services → Energy Usage**.
   Confirm the existing configuration entry and electricity/gas meters remain.
3. Open **Settings → Tools → Statistics** and confirm the existing usage
   statistics are still present, without new errors.
4. Check the Energy Dashboard and Explorer for a historical date that already
   had observations before the upgrade. A missing period must remain missing.
5. If the integration fails to load, check Home Assistant logs before making
   any configuration or Recorder changes. Do not rerun the initial import to
   repair an upgrade failure.

The upgrade is complete when the installed version is 0.1.2 and the existing
configuration and historical usage remain available.
