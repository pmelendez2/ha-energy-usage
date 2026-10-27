# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Prevent duplicate initial imports while Recorder writes are pending."""


class InitialImportBlocked(ValueError):
    """The initial import cannot safely be queued again."""


def check_initial_import(pending, key, history_exists):
    """Allow a new import only if no rows or pending job are known.

    A queued Recorder write is asynchronous. An empty database query
    cannot prove that an earlier queued write has failed. Never expire
    its marker based on elapsed time.
    """
    if history_exists:
        pending.discard(key)
        raise InitialImportBlocked(
            "History already exists; no import was performed"
        )
    if key in pending:
        raise InitialImportBlocked(
            "Earlier import is still unconfirmed. Check Home Assistant "
            "Statistics and Recorder logs. If no history persists, "
            "restart Home Assistant before retrying."
        )

