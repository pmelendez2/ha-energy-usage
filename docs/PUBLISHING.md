<!-- SPDX-License-Identifier: MIT -->
# Publishing Energy Usage for Home Assistant

> **Audience:** Developers and maintainers
> **Purpose:** Publishing Energy Usage for Home Assistant reference for Energy Usage.
> **Status:** Current documentation baseline
> **Release:** 0.1.0
> **Last Updated:** 2026-10-23

`ha_energy_usage` is a custom integration, not part of Home Assistant Core.

1. Run local tests and GitHub Actions, including supported Home Assistant
   versions. Do not claim a version is tested without completing runtime tests.
2. Commit and push the repository; create a version tag consistent with the
   version in `custom_components/energy_usage/manifest.json`.
3. Publish a GitHub Release for that tag. HACS can install custom integrations
   from their GitHub repository after users add it as a custom repository.
4. For manual installation, copy `custom_components/energy_usage/` into the
   Home Assistant configuration's `custom_components/` directory and restart.
5. Offer the repository for HACS default catalog inclusion only after meeting
   its validation, documentation, and branding requirements.

As of Home Assistant 2026.3, local brand images under the integration's
`brand/` directory take precedence over hosted images. The draft icon in this
repository should be approved before a public release.

**Version 0.1.0 limitations:** Explicit initial Recorder import is supported
for previously empty statistic series. Automatic incremental updates,
revision-aware corrections, and solar production/export ingestion are not.

## Release gates

- Verify Python and bundled Explorer tests, package contents, and documentation links.
- Run HACS Action and hassfest without ignored failures.
- Confirm `manifest.json` version matches the signed `v0.1.0` tag.
- Publish a **full GitHub Release**, not only a Git tag.
- Test HACS custom-repository installation before catalog submission.
