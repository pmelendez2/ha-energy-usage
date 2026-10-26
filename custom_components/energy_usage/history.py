# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Project Contributors
"""Validate resolved Energy Ingest intervals for historical synchronization.

This module deliberately does not write Home Assistant Recorder statistics.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any


class HistoryValidationError(ValueError):
    """The upstream interval stream cannot be safely synchronized."""


@dataclass(frozen=True)
class UsageInterval:
    """One resolved, revision-provenanced consumption interval."""

    start_utc: datetime
    end_utc: datetime
    value: Decimal
    unit: str
    revision_id: int


def normalize_stream(
    stream: dict[str, Any],
    *,
    commodity: int,
) -> list[UsageInterval]:
    """Normalize accepted values without guessing missing measurements.

    Electricity: Green Button Wh (72) -> kWh.
    Natural gas: Green Button therm (169) -> therm.
    Do not round, bucket, or shift provider timestamps here.
    """
    if stream.get("resolved") is not True or stream.get("issues"):
        raise HistoryValidationError("Meter stream is not resolved")

    if commodity == 1:
        expected_unit = 72
        output_unit = "kWh"
        conversion = Decimal("0.001")
    elif commodity == 7:
        expected_unit = 169
        output_unit = "therm"
        conversion = Decimal("1")
    else:
        raise HistoryValidationError("Unsupported commodity")

    intervals = stream.get("intervals")
    if not isinstance(intervals, list):
        raise HistoryValidationError("Missing interval collection")

    result: list[UsageInterval] = []
    keys: set[tuple[datetime, int]] = set()

    for item in intervals:
        try:
            if int(item["unit_of_measure"]) != expected_unit:
                raise HistoryValidationError("Unexpected unit of measure")

            raw = item["raw_value"]
            exponent = item["power_of_ten_multiplier"]
            duration = item["duration_seconds"]
            revision = item["accepted_revision_id"]
            if any(type(v) is not int for v in (
                raw, exponent, duration, revision
            )):
                raise HistoryValidationError("Invalid interval fields")
            if duration <= 0 or revision <= 0:
                raise HistoryValidationError("Invalid interval metadata")
            if exponent < -12 or exponent > 12:
                raise HistoryValidationError("Unexpected multiplier")

            stamp = item["start_utc"]
            if not isinstance(stamp, str) or not stamp.endswith("Z"):
                raise HistoryValidationError("Timestamp must be UTC")
            start = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            if start.tzinfo != timezone.utc:
                raise HistoryValidationError("Timestamp must be UTC")
            end = start + timedelta(seconds=duration)
            key = (start, duration)
            if key in keys:
                raise HistoryValidationError("Duplicate resolved interval")
            keys.add(key)

            value = (
                Decimal(raw) * (Decimal(10) ** exponent) * conversion
            )
        except (KeyError, TypeError, OverflowError) as exc:
            raise HistoryValidationError("Invalid upstream interval") from exc
        except ValueError as exc:
            if isinstance(exc, HistoryValidationError):
                raise
            raise HistoryValidationError("Invalid interval timestamp") from exc

        result.append(UsageInterval(
            start_utc=start,
            end_utc=end,
            value=value,
            unit=output_unit,
            revision_id=revision,
        ))

    result.sort(key=lambda item: item.start_utc)
    for previous, current in zip(result, result[1:]):
        if commodity == 1 and current.start_utc < previous.end_utc:
            raise HistoryValidationError(
                "Overlapping resolved intervals"
            )

    return result
