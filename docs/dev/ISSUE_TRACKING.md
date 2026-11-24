<!-- SPDX-License-Identifier: MIT -->
# GitHub Issue and Release Tracking

**Audience:** Contributors and release maintainers

**Purpose:** Link verified Home Assistant integration changes to issues,
release milestones, pull requests, and published releases.

**Status:** Current documentation baseline

**Release:** 0.1.5

**Last Updated:** 2026-11-23

## Workflow

1. Open an issue with acceptance criteria for tracked bugs and features.
2. Assign the issue to the intended release milestone (`vX.Y.Z`).
3. Work on a `feature/*` or `fix/*` branch with signed commits.
4. Link the issue in the PR using `Fixes #NUMBER` when the PR fully fixes it;
   otherwise use `Refs #NUMBER`, without triggering premature closure.
5. Require protected-main `isolated` CI, use a conventional merge commit,
   and keep HACS/Hassfest/compatibility checks in place.
6. For new releases, add `### Issues resolved` to the current version section
   in `CHANGELOG.md`, with direct links of the form
   `[#123 — Description](https://github.com/pmelendez2/ha-energy-usage/issues/123)`.
   Use `None` when there were no resolved issues. Mention related PRs
   separately, and reconcile milestones against the actual released changes.
7. Publish only after documented runtime, package, upgrade, and release
   verification; a closed issue does not prove code was released.

## Compatibility with current documentation

`CHANGELOG.md` is the authoritative release history; do not replace it or
rewrite historical release entries. The automated link requirement begins
with release 0.1.6, leaving the in-progress 0.1.5 release notes unchanged.
Release metadata remains synchronized through the existing
`release/VERSION` and documentation-version tools.

`python3 scripts/check_documentation.py` invokes the issue-link validator.
It checks formatting, duplicates, and mismatches, not whether a GitHub issue
was actually fixed or assigned the correct milestone. Reviewers verify those
claims in GitHub before approval.
