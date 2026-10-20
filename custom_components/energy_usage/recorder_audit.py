# SPDX-License-Identifier: MIT
"""Read-only Recorder comparison for owned hourly external statistics.

No API writes, metadata changes, or checkpoint updates occur here.
The caller must supply a COMPLETE Recorder read-back of the selected series;
a short or truncated result must not be interpreted as an empty series.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import isclose, isfinite
from typing import Mapping, Sequence

from .recorder_bridge import RecorderImportBatch, RecorderSafetyError


@dataclass(frozen=True)
class RecorderAudit:
    """The differences between planned and stored cumulative statistics."""

    statistic_id: str
    missing: tuple[datetime, ...]
    unexpected: tuple[datetime, ...]
    mismatched: tuple[datetime, ...]

    @property
    def matches(self) -> bool:
        """True only when the complete stored series matches the plan."""
        return not (self.missing or self.unexpected or self.mismatched)


def _timestamp(value: object) -> datetime:
    """Parse Recorder UTC datetime or numeric epoch timestamp."""
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise RecorderSafetyError("Non-UTC Recorder timestamp")
        stamp = value.astimezone(timezone.utc)
    elif (isinstance(value, (float, int))
          and not isinstance(value, bool) and isfinite(value)):
        try:
            stamp = datetime.fromtimestamp(value, timezone.utc)
        except (OverflowError, OSError, ValueError) as exc:
            raise RecorderSafetyError("Invalid Recorder epoch") from exc
    else:
        raise RecorderSafetyError("Invalid Recorder timestamp")
    if (stamp.minute or stamp.second or stamp.microsecond):
        raise RecorderSafetyError("Recorder hour is not aligned")
    return stamp


def _index(rows: Sequence[Mapping]) -> dict[datetime, float]:
    """Build a strict read-back index; duplicates must fail closed."""
    result: dict[datetime, float] = {}
    for row in rows:
        stamp = _timestamp(row.get("start"))
        amount = row.get("sum")
        if (not isinstance(amount, (int, float))
                or isinstance(amount, bool) or not isfinite(amount)
                or amount < 0 or stamp in result):
            raise RecorderSafetyError("Invalid or duplicate Recorder row")
        result[stamp] = float(amount)
    return result


def audit_recorder_series(
    batch: RecorderImportBatch,
    stored: Sequence[Mapping],
    *,
    complete_readback: bool,
    tolerance: float = 1e-8,
) -> RecorderAudit:
    """Detect drift, never change Recorder or infer missing usage.

    complete_readback asserts that all rows of the owned series were read.
    It is a caller obligation, NOT proof supplied by this function.
    Do not use the result to authorize destructive repair without a separate
    ownership, backup, and replace/recovery protocol.
    """
    if not complete_readback:
        raise RecorderSafetyError("Complete Recorder read-back required")
    if (not batch.statistic_id.startswith("energy_usage:electricity_meter_")
            or batch.metadata.get("source") != "energy_usage"
            or batch.metadata.get("statistic_id") != batch.statistic_id):
        raise RecorderSafetyError("Statistic ownership not established")
    if not isfinite(tolerance) or tolerance < 0:
        raise RecorderSafetyError("Invalid numeric tolerance")
    expected = _index(batch.rows)
    current = _index(stored)
    old_keys, new_keys = set(current), set(expected)
    mismatched = tuple(sorted(
        key for key in old_keys & new_keys
        if not isclose(current[key], expected[key],
                       rel_tol=0.0, abs_tol=tolerance)
    ))
    return RecorderAudit(
        batch.statistic_id,
        tuple(sorted(new_keys - old_keys)),
        tuple(sorted(old_keys - new_keys)),
        mismatched,
    )
