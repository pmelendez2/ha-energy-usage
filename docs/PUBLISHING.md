<!-- SPDX-License-Identifier: MIT -->
# Publishing Energy Usage for Home Assistant

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

**Not supported by this release:** automatic historical Recorder writes and
solar import/export sensors. Document actual functionality honestly.
