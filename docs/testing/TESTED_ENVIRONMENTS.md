<!-- SPDX-License-Identifier: MIT -->
# Tested Environments

**Audience:** Users, testers, developers, and maintainers

**Purpose:** Record reproducible Energy Usage compatibility evidence and its limits.

**Status:** v0.1.0 production verified; v0.1.1 not yet runtime validated

**Release:** 0.1.2

**Last Updated:** 2026-10-23

## Verification scope

This document records environments and outcomes **actually reported or run**
for Energy Usage 0.1.0. It distinguishes isolated automated checks from
Home Assistant runtime verification. A passing unit test does not establish
compatibility with every Home Assistant version or Linux distribution.

## Recorded environments

| Environment | Version / platform | Verification evidence | Status |
| --- | --- | --- | --- |
| Developer workstation (`sparta`) | Ubuntu 26.04, Python 3.14 virtual environment | Python test suite, integration metadata validation, JavaScript checks | Tested locally |
| Development Home Assistant (`ha-energy-dev`) | Home Assistant Container on `sparta`, port 8124; exact Core version not independently captured for this release | Integration configured with electricity and gas meters; Recorder statistics imported; Energy Dashboard and Explorer UI exercised | Runtime-tested in development |
| Development baseline documented by project | Home Assistant Core 2026.9.4; Frontend 20260826.7 | Versions recorded in [Test Plan](TEST_PLAN.md); do not assume this is the currently running dev-container build without confirming | Version baseline, not a distinct tested environment |
| Energy Ingest backend | Version 0.1.5 release candidate used in integration verification | Authenticated meter/history API, electricity and gas windows, DST handling | Integration dependency exercised; not a HA compatibility certification |
| Production `piha` | Home Assistant Container (Swarm), `hass_homeassistant`; Energy Ingest API `0.1.5-rc.3`; 2026-10-26 | v0.1.0 installed through HACS custom repository, 2 discovered meter devices, initial Recorder imports, electricity and gas Energy Dashboard graphs, Explorer card | Verified production installation and consumption-history display; Home Assistant Core version not recorded in the session |

## Verified test results

| Check | Recorded result | Scope |
| --- | --- | --- |
| Python tests (working tree before pre-release documentation patch) | 115 passed, 17 subtests passed | Integration logic, histories, and static-resource regression tests |
| Python tests (pre-release update snapshot) | 116 passed, 17 subtests passed | Same suite plus documentation-related regression coverage |
| Explorer JavaScript checks | 51 checks passed | Chart logic, axes, detail selection, and navigation |
| Integration metadata/branding validation | PASS | Manifest, JSON, and bundled brand assets |
| Explorer static HTTP resource | HTTP 200 | `/energy_usage/energy-usage-explorer.js?v=0.1.0` on development Home Assistant |
| Explorer UI manual verification | PASS | Hourly bars, line charts, date navigation, selected observation details |
| Home Assistant Energy Dashboard | Verified in development | Electricity in kWh and gas in thm; no invented missing readings |
| Production history and graphs, 2026-10-26 | Both commodities passed manual visual verification | Electricity: 9,480 hourly readings; gas: 395 daily readings; both resolved with no issues; 2 devices and Energy Dashboard/Explorer visible |
| HACS release checks for v0.1.0 | 10 PR checks passed, 0 failing | HACS, hassfest, CI and Python compatibility checks as reported by maintainer |

The development Recorder checks exercised **initial historical import**. They
must not be interpreted as verification of automatic incremental sync,
correction-safe reimport into existing series, or automatic gap filling.

## Not yet verified

- Home Assistant Core versions other than the development baseline shown above.
- Different Home Assistant installation methods or host operating systems.
- Upgrade behavior from v0.1.0 to v0.1.1, which is not yet released.
- HACS default-catalog approval (custom-repository installation is verified).

## Evidence required for each new tested environment

Before adding a row marked *Tested*, record the following:

1. Release/tag or commit under test and verification date.
2. Home Assistant Core and Frontend versions, installation method,
   Python runtime, operating system, and hardware architecture.
3. Energy Ingest API version and configuration used for the test (without
   storing credentials or private customer data).
4. Exact commands, CI run links, or manual test-case references and results.
5. Electricity and natural gas observations exercised, including gaps,
   daylight-saving transitions, and Recorder/Energy Dashboard behavior.
6. Known failures and restrictions, and who approved the evidence.

Record detailed cases in [Test Plan](TEST_PLAN.md) and
[Test Strategy](TEST_STRATEGY.md). For maintainer release steps, see
[Release Verification](../dev/RELEASE_VERIFICATION.md).
