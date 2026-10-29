# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Verify Recorder persistence only after an explicit completion barrier.

The barrier must be supplied by a Home Assistant-version-specific adapter.
A queued external-statistics import is not a completed database transaction.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable, Sequence

from .statistics_sync_plan import StatisticsSyncError
from .statistics_sync_verify import (
    SyncVerification,
    verify_sync_persistence,
)


async def verify_after_recorder_commit(
    hass,
    statistic_id: str,
    expected: Sequence[dict],
    *,
    wait_for_commit: Callable[[], Awaitable[None]],
    read_statistics=None,
) -> SyncVerification:
    """Wait for an authoritative queue barrier, then verify complete history.

    Callers must use a recorder-supported completion barrier known to include
    the import job. Do not substitute arbitrary sleeps or startup events.
    Failed barriers and mismatches propagate; they are never reported as
    successful synchronization.
    """
    if not expected or not statistic_id.startswith("energy_usage:"):
        raise StatisticsSyncError("Invalid synchronization verification")
    if not callable(wait_for_commit):
        raise StatisticsSyncError("Recorder completion barrier required")
    if read_statistics is None:
        from .statistics_sync_recorder import read_owned_statistics

        read_statistics = read_owned_statistics

    await wait_for_commit()
    starts = [row["start"] for row in expected]
    if any(not isinstance(stamp, datetime) or stamp.tzinfo is None
           for stamp in starts):
        raise StatisticsSyncError("Expected timestamps must be aware")
    beginning = datetime(1970, 1, 1, tzinfo=timezone.utc)
    ending = max(starts) + timedelta(days=2)
    stored = await read_statistics(hass, statistic_id, beginning, ending)
    return verify_sync_persistence(
        statistic_id,
        expected,
        stored,
        complete_readback=True,
    )




import asyncio
from datetime import datetime, timedelta, timezone



async def wait_for_persisted_statistics(
    hass, statistic_id, expected, *, read_statistics=None,
    attempts=40, interval=0.25, sleep=asyncio.sleep,
):
    """Require an exact full read-back, never infer success from queueing.

    Recorder imports are asynchronous. A completed read-back is the proof;
    polling is bounded and is not itself treated as a completion barrier.
    """
    if not expected or not statistic_id.startswith("energy_usage:"):
        raise StatisticsSyncError("Invalid persistence verification")
    if attempts < 1 or interval < 0:
        raise StatisticsSyncError("Invalid persistence retry policy")
    if read_statistics is None:
        from .statistics_sync_recorder import read_owned_statistics
        read_statistics = read_owned_statistics
    beginning = datetime(1970, 1, 1, tzinfo=timezone.utc)
    ending = max(datetime.now(timezone.utc), expected[-1]["start"])
    ending += timedelta(days=2)
    last_mismatch = None
    for attempt in range(attempts):
        # Reader exceptions are not transient mismatches: surface failures.
        stored = await read_statistics(
            hass, statistic_id, beginning, ending
        )
        try:
            return verify_sync_persistence(
                statistic_id, expected, stored, complete_readback=True,
            )
        except StatisticsSyncError as exc:
            last_mismatch = exc
        if attempt + 1 < attempts:
            await sleep(interval)
    raise StatisticsSyncError(
        "Recorder did not persist the verified canonical statistics"
    ) from last_mismatch
