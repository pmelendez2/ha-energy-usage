<!-- SPDX-License-Identifier: MIT -->
# HACS Default Catalog Submission

**Audience:** Developers and maintainers

**Purpose:** Track external HACS catalog requirements and evidence

**Status:** Submission preparation; not yet catalog-approved

**Release:** 0.1.2

**Last Updated:** 2026-10-26

Installing through a custom HACS repository is already validated; being
listed in the **default HACS catalog** requires external review. This is
not Home Assistant Core inclusion or an official Home Assistant endorsement.

## Repository readiness

- [x] Public source repository with a single integration in
  `custom_components/energy_usage`.
- [x] `hacs.json` supplies the display name and renders `README.md`.
- [x] `manifest.json` provides the required integration metadata.
- [x] Signed `v0.1.0` tag and full GitHub Release published.
- [x] HACS Action and hassfest passed on the release pull request.
- [x] Production custom-repository install and runtime graphs verified
  on `piha`, 2026-10-26.
- [ ] Confirm GitHub repo description, topics, and Issues enabled.
- [x] Local `custom_components/energy_usage/brand/icon.png` and
  `icon@2x.png` included.
- [ ] Confirm the **Brands** check on the actual `hacs/default` PR.
  HACS documentation still references `home-assistant/brands`, while
  newer submission checks may accept locally bundled branding.
  If the check requires a Brands submission, complete that separately.
- [ ] Publish any pending UX improvements as a reviewed versioned release.
- [ ] Submit `pmelendez2/ha_energy_usage` to `hacs/default` via an editable
  pull request from the repository owner's personal fork/branch.
- [ ] Wait for all default-catalog PR checks and maintainer approval.
- [ ] Confirm the integration appears after the HACS catalog scan.

## Submission references

- [HACS default repositories](https://www.hacs.dev/docs/publish/include/)
- [HACS submission source](https://github.com/hacs/documentation/blob/main/source/docs/publish/include.md)
- [HACS integration requirements](https://www.hacs.dev/docs/publish/integration/)
- [HACS publisher requirements](https://www.hacs.dev/docs/publish/start/)
- [Home Assistant Brands](https://github.com/home-assistant/brands)

Do not represent passing CI, a custom HACS installation, or this checklist
as acceptance into the default HACS catalog.
