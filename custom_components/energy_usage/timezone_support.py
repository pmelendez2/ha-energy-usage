# SPDX-License-Identifier: MIT
"""Obtain Home Assistant's already-configured local timezone object."""

from __future__ import annotations

from datetime import tzinfo


def home_assistant_timezone() -> tzinfo:
    """Return HA's current timezone without loading ZoneInfo on the event loop."""
    from homeassistant.util import dt as dt_util

    local_tz = dt_util.get_default_time_zone()
    if not isinstance(local_tz, tzinfo):
        raise ValueError("Home Assistant time zone is not configured")
    return local_tz
