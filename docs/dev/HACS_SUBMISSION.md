<!-- SPDX-License-Identifier: MIT -->
# HACS Default Catalog Submission

**Audience:** Developers and maintainers

**Purpose:** Record HACS catalog acceptance and outstanding validation.

**Status:** Accepted into default HACS catalog; partial production runtime verified

**Release:** 0.1.5

**Last Updated:** 2026-11-23

## HACS catalog acceptance

The integration `pmelendez2/ha-energy-usage` was admitted to the default
HACS integration catalog when
[hacs/default PR #13425](https://github.com/hacs/default/pull/13425)
merged on **November 9, 2026**. The integration is present in the catalog.
The earlier [PR #12817](https://github.com/hacs/default/pull/12817)
is historical submission/review context, not the active acceptance PR.

Users install by searching for **Energy Usage** directly within HACS.
Custom-repository instructions are no longer required for new users.
Catalog inclusion is distinct from Home Assistant Core inclusion and is
not certification of every runtime deployment configuration.

## Current release and compatibility evidence

- Energy Usage **v0.1.5** was published November 5, 2026.
- Energy Ingest **v0.1.10** is the recommended current backend release.
- Energy Ingest **v0.1.9-rc.3** was the recorded guided-import
  interoperability test baseline; later stable v0.1.9 also exists.
- On November 23, 2026, a production v0.1.10 plus v0.1.5 test verified
  backend XML import, resource association, read-only preflight, and
  append-only Recorder synchronization for electricity and gas.
- Scheduled retries, actual corrections, API outages and rollback are
  not fully accepted by this test.
- Previous HACS, Hassfest, and Python CI successes are not a substitute for
  production upgrade, rollback, outage, and restart acceptance.

## Remaining acceptance tasks

- [ ] Verify HACS default-catalog installation in a clean supported
  Home Assistant environment.
- [x] Record v0.1.10 + v0.1.5 production import/synchronization evidence.
- [ ] Verify v0.1.10 correction handling, retries and outage recovery.
- [ ] Verify production upgrade and rollback without altering Recorder history.
- [ ] Complete documented failure-recovery and multi-meter test cases.

## References

- [HACS integration installation](https://www.hacs.xyz/docs/use/)
- [HACS publishing requirements](https://www.hacs.dev/docs/publish/integration/)
- [Home Assistant Brands](https://github.com/home-assistant/brands)
- [Release verification](RELEASE_VERIFICATION.md)
