<!-- SPDX-License-Identifier: MIT -->
# Home Assistant Integration Release Verification

> **Audience:** Developers and maintainers
> **Purpose:** Home Assistant Integration Release Verification reference for Energy Usage.
> **Status:** Current documentation baseline
> **Release:** 0.1.0
> **Last Updated:** 2026-10-23

**Purpose:** Define repeatable test, package, and release verification.

**Intended Audience:** Energy Usage developers and maintainers.

## Local verification

Run from the `ha_energy_usage` repository root:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m pytest -q
python3 -m compileall -q custom_components/energy_usage tests
python3 scripts/check_integration.py
python3 scripts/package_release.py --output /tmp/ha-energy-usage.zip
python3 scripts/check_release_package.py /tmp/ha-energy-usage.zip
node --check custom_components/energy_usage/www/energy-usage-explorer.js
node tests/test-energy-usage-explorer.cjs
python3 scripts/check_documentation.py
git diff --check
```

The CI `isolated` job runs the same checks. The independent Python
compatibility matrix covers 3.13 and 3.14. Neither constitutes a real
Home Assistant runtime integration test.

## Development runtime acceptance

Test with a disposable Home Assistant instance, using the published
Energy Ingest HTTP API and a development-only bearer token. Confirm
successful setup, two meter devices, sensor state, failure/recovery,
and reload/unload. Explicit initial Recorder imports have been runtime-validated. Automatic
correction-safe synchronization remains outside version 0.1.0.

## Publishing

Use a feature branch and signed commits, then a pull request and required
CI checks before merging into protected `main`. GitHub release tags must
match the `manifest.json` version. For HACS installation use the GitHub
repository; the component-only ZIP is an optional manual-install artifact.
