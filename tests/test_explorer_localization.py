# SPDX-License-Identifier: MIT
"""Smoke-check the first-release Explorer localization foundation."""
from pathlib import Path


EXPLORER = (
    Path(__file__).resolve().parents[1]
    / "custom_components/energy_usage/www/energy-usage-explorer.js"
)


def test_english_labels_have_a_central_lookup():
    source = EXPLORER.read_text(encoding="utf-8")
    assert "const EXPLORER_LABELS" in source
    assert "function explorerLabel(key)" in source
    for label in ("Start date", "End date", "Group by", "Calculation",
                  "Use latest available", "Jump to day (hourly)"):
        assert f'explorerLabel("{label}")' in source
