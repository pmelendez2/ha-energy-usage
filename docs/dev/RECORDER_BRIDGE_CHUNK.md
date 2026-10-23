<!-- SPDX-License-Identifier: MIT -->

# ADR-0001 Recorder adapter: guarded initial import

> **Audience:** Developers and maintainers
> **Purpose:** ADR-0001 Recorder adapter: guarded initial import reference for Energy Usage.
> **Status:** Current documentation baseline
> **Release:** 0.1.0
> **Last Updated:** 2026-10-23

Status: development-only; NOT activated during Home Assistant setup.

## Scope

- `recorder_bridge.py` prepares an approved import of hourly electricity
  statistics only when a trusted full-series Recorder query has shown no
  existing statistic rows **and** metadata ownership has been checked.
- Uses Home Assistant's `async_add_external_statistics` API to enqueue the
  imported rows. Enqueueing is NOT proof of persistence.
- `verify_import` compares read-back timestamps and cumulative sums.
- No automatic import, clearing, correction, or rebuilding is enabled.
- Does not touch `energy_ingest` or the production Home Assistant instance.

## Important safeguards and limitations

`prepare_initial_import` takes `existing` as a supplied argument. An empty
list passed by a caller is NOT proof that a series is absent. Before calling
`queue_initial_import`, the caller must implement a trusted full-series
readback and check Recorder metadata (including possible empty metadata).
This missing integration is why this adapter is not yet wired into startup.

The current statistics planner represents missing complete hours only when
partial readings were supplied. Entirely absent hours also remain missing,
but an external data-coverage audit is necessary to establish the complete
window and any missing full-hour periods.

The existing planner uses cumulative observed totals; a complete restartable
rebuild protocol must reconcile missing observations, correction offsets,
prior Recorder metadata, and interruption recovery before being enabled.

Gas daily reporting and daylight-saving-time mapping are not implemented.
No storage tables or Recorder SQL are modified by this chunk.

## Test commands on sparta

From `/home/pme991/src/ha_energy_usage`:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
git diff --check
git status --short
```

## Next phase

Create a bounded readback interface against the installed HA Core version,
verify namespace ownership and metadata, and perform an explicit opt-in
single-meter import in a disposable HA development database. Verify completion
with readback. Then design and test correction/rebuild as a distinct workflow.
