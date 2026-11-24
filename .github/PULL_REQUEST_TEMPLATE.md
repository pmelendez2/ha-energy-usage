<!-- SPDX-License-Identifier: MIT -->
<!--
**Audience:** Contributors and reviewers
**Purpose:** Capture issue, testing, security and release evidence for a PR.
**Status:** Maintained template
**Release:** 0.1.5
**Last Updated:** 2026-11-23
-->
# Pull request

## Summary

Describe the change in plain language.

## Linked issues and milestone

- Fixes #ISSUE_NUMBER (or `None` if not issue-driven)
- Target milestone: `vX.Y.Z` (or `None`)

## Verification

List actual unit, Python compatibility, HACS, Hassfest, package, and
Home Assistant runtime checks. Distinguish completed tests from pending tests.

## Security and privacy

Describe effects on credentials, utility XML, meter identifiers, and Recorder.
Do not attach customer data, tokens, or private deployment details.

## Release impact

- [ ] CHANGELOG and linked issues updated, or not applicable
- [ ] Upgrade compatibility documented, or no change
- [ ] Signed commit and required `isolated` CI verified
