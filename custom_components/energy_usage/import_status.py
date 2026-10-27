# SPDX-License-Identifier: MIT
"""Track initial-import attempts without mistaking a queue for success."""

from datetime import datetime, timezone


_ATTEMPTS = {}


def key_for(entry_id, meter_id):
    """Identify one meter in one integration entry."""
    return (entry_id, int(meter_id))


def started(key):
    """Record that an initial import is being attempted."""
    _ATTEMPTS[key] = {
        "last_attempt": "Importing",
        "last_error": None,
        "last_attempt_at": datetime.now(timezone.utc).isoformat(),
        "last_success_at": _ATTEMPTS.get(key, {}).get(
            "last_success_at"
        ),
    }


def queued(key):
    """Recorder accepted the job, but persistence is unconfirmed."""
    _ATTEMPTS[key]["last_attempt"] = "Awaiting Recorder"


def failed(key, reason):
    """Store the error without erasing previously confirmed history."""
    previous = _ATTEMPTS.get(key, {})
    _ATTEMPTS[key] = {
        **previous,
        "last_attempt": "Failed",
        "last_error": str(reason),
        "last_attempt_at": previous.get(
            "last_attempt_at", datetime.now(timezone.utc).isoformat()
        ),
    }


def snapshot(key, has_history):
    """Return a state only after considering persisted Recorder rows."""
    attempt = _ATTEMPTS.get(key, {})
    if has_history and attempt.get("last_attempt") == "Awaiting Recorder":
        attempt["last_attempt"] = "Succeeded"
        attempt["last_success_at"] = datetime.now(
            timezone.utc
        ).isoformat()
    if has_history:
        state = "Imported"
    elif attempt.get("last_attempt") in (
        "Importing", "Awaiting Recorder"
    ):
        state = "Importing"
    elif attempt.get("last_attempt") == "Failed":
        state = "Failed"
    else:
        state = "Not imported"
    return state, dict(attempt)


def attempt_details(key):
    """Read the latest attempt without inferring Recorder persistence."""
    return dict(_ATTEMPTS.get(key, {}))


def clear_entry(entry_id):
    """Forget volatile attempt state when the integration unloads."""
    for key in tuple(_ATTEMPTS):
        if key[0] == entry_id:
            del _ATTEMPTS[key]
