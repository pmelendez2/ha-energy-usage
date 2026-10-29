# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""User-owned scheduling preferences for canonical usage reconciliation."""

CONF_SYNC_HOURS = "sync_interval_hours"
CONF_SYNC_STARTUP = "sync_on_startup"
DEFAULT_SYNC_HOURS = 24
DEFAULT_SYNC_STARTUP = True
SYNC_INTERVAL_CHOICES = {
    6: "Every 6 hours",
    12: "Every 12 hours",
    24: "Daily (24 hours)",
    168: "Weekly (7 days)",
}


def sync_preferences(entry):
    """Return validated preferences, defaulting older installations."""
    options = entry.options
    hours = options.get(CONF_SYNC_HOURS, DEFAULT_SYNC_HOURS)
    if type(hours) is not int or hours not in SYNC_INTERVAL_CHOICES:
        raise ValueError("Unsupported synchronization interval")
    startup = options.get(CONF_SYNC_STARTUP, DEFAULT_SYNC_STARTUP)
    if type(startup) is not bool:
        raise ValueError("Invalid startup synchronization setting")
    return hours, startup
