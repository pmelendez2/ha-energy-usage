<!-- SPDX-License-Identifier: MIT -->
# Tested Environments

**Audience:** Users, testers, developers, and maintainers

**Purpose:** Record reproducible Energy Usage compatibility evidence and its limits.

**Status:** Historical and November 2026 production evidence; recovery acceptance incomplete

**Release:** 0.1.5

**Last Updated:** 2026-11-23

## Verification scope

This document records environments and outcomes **actually reported or run**
for historical releases and v0.1.5 preparation. It distinguishes
isolated automated checks from
Home Assistant runtime verification. A passing unit test does not establish
compatibility with every Home Assistant version or Linux distribution.

## Recorded environments

| Environment | Version / platform | Verification evidence | Status |
| --- | --- | --- | --- |
| Developer workstation (`sparta`) | Ubuntu 26.04, Python 3.14 virtual environment | Python test suite, integration metadata validation, JavaScript checks | Tested locally |
| Development Home Assistant (`ha-energy-dev`) | Home Assistant Container 2026.10.1 on `sparta`, port 8124 (2026-11-04) | Canonical Explorer and Utility Card HTTP 200; removed Explorer alias HTTP 404; HTTP utility URL accepted; both cards displayed | v0.1.4 code runtime-tested in development |
| Development baseline documented by project | Home Assistant Core 2026.9.4; Frontend 20260826.7 | Versions recorded in [Test Plan](TEST_PLAN.md); do not assume this is the currently running dev-container build without confirming | Version baseline, not a distinct tested environment |
| Energy Ingest backend | Version 0.1.5 release candidate used in integration verification | Authenticated meter/history API, electricity and gas windows, DST handling | Integration dependency exercised; not a HA compatibility certification |
| Production `piha` | Home Assistant Container (Swarm), `hass_homeassistant`; Energy Ingest API `0.1.5-rc.3`; 2026-10-26 | Earlier installation through HACS custom repository, 2 discovered meter devices, initial Recorder imports, electricity and gas Energy Dashboard graphs, Explorer card | Historical production evidence; not v0.1.2 upgrade acceptance |

## Verified test results

| Check | Recorded result | Scope |
| --- | --- | --- |
| Python tests (working tree before pre-release documentation patch) | 115 passed, 17 subtests passed | Integration logic, histories, and static-resource regression tests |
| Python tests (pre-release update snapshot) | 116 passed, 17 subtests passed | Same suite plus documentation-related regression coverage |
| v0.1.4 preparation Python tests | 263 passed | Integration, resource, and Utility Card regressions |
| Explorer JavaScript checks | 51 checks passed | Chart logic, axes, detail selection, and navigation |
| Integration metadata/branding validation | PASS | Manifest, JSON, and bundled brand assets |
| Explorer static HTTP resource | HTTP 200 | Canonical `/energy-usage/energy-usage-explorer.js` in development; removed underscore-path alias returns 404 |
| Explorer UI manual verification | PASS | Hourly bars, line charts, date navigation, selected observation details |
| Home Assistant Energy Dashboard | Verified in development | Electricity in kWh and gas in thm; no invented missing readings |
| Production history and graphs, 2026-10-26 | Both commodities passed manual visual verification | Electricity: 9,480 hourly readings; gas: 395 daily readings; both resolved with no issues; 2 devices and Energy Dashboard/Explorer visible |
| HACS release checks | 10 PR checks passed, 0 failing in the recorded historical run | HACS, hassfest, CI and Python compatibility checks; not independent v0.1.2 evidence |
| v0.1.4 preparation PR #10 | 10 checks passed, 0 failed | Isolated CI, HACS, Hassfest, Python 3.13 and 3.14; not production upgrade evidence |
| v0.1.5 + Energy Ingest v0.1.10 on `piha` (2026-11-23) | 499 Recorder additions; zero duplicate timestamps | Production import, meter matching, preflight and manual synchronization; limits below |

The historical Recorder checks cited above primarily exercised initial
import, not the full v0.1.5 correction-safe synchronization acceptance
matrix. Later development tests exercised correction-safe synchronization,
but do not prove every production outage or restart scenario. Missing
readings must never be automatically filled.

## Not yet verified

- Home Assistant Core versions other than the development baseline shown above.
- Different Home Assistant installation methods or host operating systems.
- Full production upgrade and recovery acceptance for v0.1.5.
- Full outage, rollback and recovery acceptance for the v0.1.10 backend.
- A default-catalog HACS install in a live target instance (catalog
  acceptance itself is confirmed by merged PR #13425).

## November 23, 2026: production v0.1.10 interoperability

On `piha`, the running Energy Ingest API image was upgraded from
v0.1.9 to v0.1.10 without replacing the MariaDB volume or token.
Home Assistant Energy Usage was upgraded from v0.1.4 to published
v0.1.5. The SDG&E electricity and gas XML files dated 2026-11-23
were imported by the backend (553 and 22 accepted source observations).
After matching resource 21 to electric meter 1 and resource 22 to gas
meter 2, 21 resources were associated: 12 electricity and 9 gas.
The 288 older pairwise electricity overlap differences were unchanged;
the new resource overlaps showed no differing values.

The read-only Home Assistant preflight found 10,153 existing electric
Recorder rows versus 10,633 canonical rows (480 additions), and 423
existing gas rows versus 442 canonical rows (19 additions). Both
reported zero corrections. After the explicit sync actions, read-only
SQLite verification found 10,633 electric rows and 442 gas rows with
zero duplicate UTC timestamps in each series. The last electricity
timestamp was 2026-11-24 07:00 UTC; gas ended 2026-11-22 08:00 UTC.
Explorer showed November 1–23 electricity and November 1–22 gas
on the dashboard after its obsolete `/energy_usage/` JavaScript URL
was changed to `/energy-usage/energy-usage-explorer.js`.

**Scope:** This confirms production API access, accepted import, meter
mapping, append-only synchronization and visible charts. It does not
prove end-to-end correction application, individual daylight-saving
hour accounting, outage/restart recovery, schedule behavior, backup
restoration, or equality of each chart aggregate with source XML.

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

## Utility upload runtime validation still required

The guided Utility Card workflow has since been exercised in development
with physical-meter mapping and Recorder synchronization. Additional
v0.1.5 target-version regression and production upgrade/recovery evidence
is still required; historical source-level checks are not sufficient
to claim complete deployment acceptance.

## Acquisition-source discovery and upload security (development)

The source catalog, administrator-only Home Assistant proxy, bounded
request reading, and Recorder retry action have contract coverage.
These checks do not establish per-source authorization within Energy Ingest:
its bearer token currently grants the same API permissions for all configured
sources. For additional release acceptance, test source-to-document association,
backend authorization boundaries, file/folder selection, and partial
failures using an isolated database and a real browser session.
