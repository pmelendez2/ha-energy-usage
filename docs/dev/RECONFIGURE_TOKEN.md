<!-- SPDX-License-Identifier: MIT -->
<!-- AI-assisted: ChatGPT / GPT-6; 2026-10-20. -->

# API Token Reconfiguration

> **Audience:** Developers and maintainers
> **Purpose:** API Token Reconfiguration reference for Energy Usage.
> **Status:** Current documentation baseline
> **Release:** 0.1.0
> **Last Updated:** 2026-10-23

**Purpose:** Describe the user-facing API token rotation workflow and
its authentication safety requirements.

**Intended Audience:** Maintainers and developers.

## Configuration behavior

An existing Energy Usage entry may have a revoked token after an Energy
Ingest reinstall. The Reconfigure form must accept both the existing
endpoint and a replacement token without validating the old token first.
Only a successful API request with the replacement token allows saving.

The configured URL remains the integration's unique identity. Changes
to a different server must not silently replace that identity. A network
failure must report *cannot connect* separately from invalid credentials.
Credentials must not appear in logs, diagnostics, or generated archives.

## Verification

Cover same-server replacement, rejected replacement, network failure,
identity mismatch, and an empty form in config-flow tests. Confirm the
real runtime form after restarting only the isolated HA development
container, not production Home Assistant.

## Limitations

Historical Recorder statistics and stream correctness are separate
milestones. Successfully saving a replacement API token does not
validate utility consumption totals or fill missing periods.
