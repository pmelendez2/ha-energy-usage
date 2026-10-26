<!-- SPDX-License-Identifier: MIT -->

# Recorder read-back audit chunk

> **Audience:** Developers and maintainers
> **Purpose:** Recorder read-back audit chunk reference for Energy Usage.
> **Status:** Current documentation baseline
> **Release:** 0.1.0
> **Last Updated:** 2026-10-23

This chunk adds `recorder_audit.py`, a **read-only** comparison of a
planned electricity statistics series with values read back from Recorder.
It reports missing, unexpected, or numerically mismatched hourly rows.
This is not a database repair engine and does not authorize deletion.

## Important limitation

`complete_readback=True` is a claim made by the caller. The adapter cannot
independently prove a query returned all Recorder rows or that metadata is
owned by this integration. The caller must verify these conditions against
the installed Home Assistant Core runtime before production use.

The existing `queue_initial_import` API queues writes but does not confirm
their completion. The future synchronization controller must establish
completion, read back, and recover after interruption before checkpoints.

No automatic Recorder imports, corrections or rebuilds are enabled.

## Validation on sparta

From `/home/pme991/src/ha_energy_usage` run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 -m compileall -q custom_components/energy_usage
git diff --check
```

Review compatibility with the installed Home Assistant version before
connecting the read-back adapter to any live statistics API.
