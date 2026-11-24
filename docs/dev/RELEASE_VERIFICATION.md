<!-- SPDX-License-Identifier: MIT -->
# Home Assistant Integration Release Verification

**Audience:** Developers and maintainers

**Purpose:** Verify integration changes and prepare signed releases.

**Status:** Current documentation baseline

**Release:** 0.1.5

**Last Updated:** 2026-11-24

## Local verification

Run from the repository root with Python 3.13 or 3.14, Node.js, Git,
Bash, and the test dependencies used by the standard CI environment
(`python3 -m pip install aiohttp PyYAML`):

```bash
bash scripts/verify-release.sh
```

The runner checks both independently maintained current versions and tagged
references, documentation links and policy, CI contracts, integration metadata,
Python compilation and regressions, Explorer JavaScript syntax and tests,
release ZIP packaging and ZIP integrity/version, and Git whitespace.
It prints each check and stops at the first failure. The generated, ignored
artifact is `build/ha-energy-usage.zip` under the repository root.

The command is safe to rerun from any directory and with local uncommitted
changes. It does not change source or version metadata, publish, commit,
push, or perform a Git history security scan. Run the separate
`bash scripts/check-publication.sh` **after committing** and before pushing;
that gate requires a clean tree and scans Git history for secrets.

The CI `isolated` job invokes the same script with the classified scope:
full for source or unknown changes, docs for documentation-only changes,
and workflow for workflow-only changes. Documentation and version checks
always run; full mode additionally runs code tests and release packaging.
The required `isolated` check is always present. HACS/Hassfest and the Python
compatibility matrix remain separate workflows. Passing source checks does
not establish live Home Assistant runtime acceptance.

The unified verification runner includes
`python3 scripts/check_documentation.py` to validate documentation
metadata, release consistency, and local links. This check is executed
by the runner and does not need to be invoked separately.

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

Run `bash scripts/verify-release.sh` before committing. After committing,
run `bash scripts/check-publication.sh` to verify a clean tree and scan
Git history for secrets, then push the feature branch. Use signed commits,
a pull request, and required CI checks before merging into protected `main`. GitHub release tags must
match the `manifest.json` version. For HACS installation use the GitHub
repository; the component-only ZIP is an optional manual-install artifact.

## Runtime acceptance and historical evidence

Run automated checks using `bash scripts/verify-release.sh`.
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
