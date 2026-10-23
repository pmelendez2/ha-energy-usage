<!-- SPDX-License-Identifier: MIT -->

# ADR-0001 implementation chunk: electricity statistics preview

> **Audience:** Developers and maintainers
> **Purpose:** ADR-0001 implementation chunk: electricity statistics preview reference for Energy Usage.
> **Status:** Current documentation baseline
> **Release:** 0.1.0
> **Last Updated:** 2026-10-23

Status: development-only, no Recorder write operations.

This chunk updates `statistics_plan.py` to accept actual subhourly
measurements, including four adjacent 15-minute electricity observations.
Only hours with exact, nonoverlapping coverage produce statistics. A
partially observed hour is reported in `incomplete_hours` and never given a
synthetic value. Completely unobserved hours are likewise absent; their
coverage must be assessed against the requested time range externally.

`statistics_preview.py` prepares an integration-owned external statistic ID
and a Recorder-shaped metadata/payload preview. Its output is not a call to
Recorder. Its cumulative sums are computed from supplied complete hours and
are anchored at zero **only for full-history previews**. Never append a
partial-range plan, use it as a recovery anchor, or import it directly.

## Validation gate before activation

- Verify the precise HA Core version and external-statistics schema in the
  running development instance on `sparta`.
- Determine whether the Energy Dashboard can represent and surface missing
  hours with the proposed external series and `sum` semantics.
- Implement explicit meter identity verification and full-range ownership.
- Implement a Recorder read/compare, safe replacement protocol, completion
  verification, persistence and restart-recovery flow before any writes.
- Validate gas day boundaries and DST separately; this module supports only
  electricity in kWh.
- Run integration-level tests against the actual HA development environment;
  standalone tests alone are not sufficient.

## Verification

From `/home/pme991/src/ha_energy_usage` on `sparta`:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
git diff --check
```

The `statistics_plan.py` change relaxes the old hourly-only assertion in
`test_statistics_plan.py`: a partial hour is now omitted rather than rejected,
while timestamps crossing hour boundaries remain rejected.
