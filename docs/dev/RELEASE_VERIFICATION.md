<!-- SPDX-License-Identifier: MIT -->
# Home Assistant Integration Release Verification

**Audience:** Developers and maintainers

**Purpose:** Verify integration changes and prepare signed releases.

**Status:** Current documentation baseline

**Release:** 0.1.5

**Last Updated:** 2026-11-24

## Local verification

Run from the `ha-energy-usage` repository root. Install the test
dependencies listed in `.github/workflows/ci.yml` before
running the unit tests; no maintainer-specific directories are used:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m compileall -q custom_components/energy_usage tests
python3 scripts/check_integration.py
python3 scripts/package_release.py --output build/ha-energy-usage.zip
python3 scripts/check_release_package.py build/ha-energy-usage.zip
node --check custom_components/energy_usage/www/energy-usage-explorer.js
node tests/test-energy-usage-explorer.cjs
python3 scripts/check_documentation.py
python3 scripts/manage_doc_versions.py --check
python3 -m unittest discover -s tests -p 'test_doc_policy.py'
git diff --check
```

The CI `isolated` job runs the standard-library test and package checks;
These commands use Python, Node.js, and files shipped in the
repository. The independent Python compatibility matrix covers
3.13 and 3.14. Neither constitutes a real
Home Assistant runtime integration test.

## Development runtime acceptance

Test with a disposable Home Assistant instance, using the published
Energy Ingest HTTP API and a development-only bearer token. Confirm
successful setup, two meter devices, sensor state, failure/recovery,
and reload/unload.

Source-level regression tests and earlier runtime checks do not prove
every shutdown, correction, outage, rollback, or upgrade scenario.
Record live acceptance against the target versions using the scenarios
in [Test Plan](../testing/TEST_PLAN.md) and the outcomes in
[Tested Environments](../testing/TESTED_ENVIRONMENTS.md).

## Publishing

Use a feature branch and signed commits, then a pull request and required
CI checks before merging into protected `main`. GitHub release tags must
match the `manifest.json` version. For HACS installation use the GitHub
repository; the component-only ZIP is an optional manual-install artifact.

## Runtime acceptance and historical evidence

Run automated checks using the commands in **Local verification**.
The full lifecycle, Recorder, and guided utility workflow acceptance
scenarios are maintained in [Test Plan](../testing/TEST_PLAN.md).
The guided workflow follows the accepted
[ADR-0003](../adr/0003-guided-physical-meter-mapping-and-import-synchronization.md).
Acceptance of an ADR does not mean every runtime scenario has passed.

Recorded interoperability versions, historical results, and current
production evidence are in
[Tested Environments](../testing/TESTED_ENVIRONMENTS.md).
Automated unit and contract tests alone do not establish full live
Home Assistant Recorder acceptance.
