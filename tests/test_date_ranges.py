# SPDX-License-Identifier: MIT
"""Regression coverage for calendar-date to UTC boundary conversion."""

from datetime import date, datetime, timezone
import importlib.util
from pathlib import Path
import unittest

PATH = (Path(__file__).resolve().parents[1] /
        "custom_components/energy_usage/date_ranges.py")
spec = importlib.util.spec_from_file_location("energy_date_ranges", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
selected_calendar_dates_utc = module.selected_calendar_dates_utc
UTC = timezone.utc


class LocalDateRangeTests(unittest.TestCase):
    def test_normal_day(self):
        actual = selected_calendar_dates_utc(
            date(2026, 10, 1), date(2026, 10, 1),
            "America/Los_Angeles"
        )
        self.assertEqual(actual, (
            datetime(2026, 10, 1, 7, tzinfo=UTC),
            datetime(2026, 10, 2, 7, tzinfo=UTC),
        ))

    def test_spring_forward_23_hours(self):
        begin, end = selected_calendar_dates_utc(
            date(2026, 3, 8), date(2026, 3, 8),
            "America/Los_Angeles"
        )
        self.assertEqual(begin, datetime(2026, 3, 8, 8, tzinfo=UTC))
        self.assertEqual(end, datetime(2026, 3, 9, 7, tzinfo=UTC))
        self.assertEqual((end - begin).total_seconds(), 23 * 3600)

    def test_fall_back_25_hours(self):
        begin, end = selected_calendar_dates_utc(
            date(2026, 11, 1), date(2026, 11, 1),
            "America/Los_Angeles"
        )
        self.assertEqual(begin, datetime(2026, 11, 1, 7, tzinfo=UTC))
        self.assertEqual(end, datetime(2026, 11, 2, 8, tzinfo=UTC))
        self.assertEqual((end - begin).total_seconds(), 25 * 3600)

    def test_includes_last_selected_date(self):
        begin, end = selected_calendar_dates_utc(
            date(2026, 10, 1), date(2026, 10, 7), "UTC"
        )
        self.assertEqual(begin, datetime(2026, 10, 1, tzinfo=UTC))
        self.assertEqual(end, datetime(2026, 10, 8, tzinfo=UTC))

    def test_rejects_reversed_dates(self):
        with self.assertRaises(ValueError):
            selected_calendar_dates_utc(
                date(2026, 10, 7), date(2026, 10, 1), "UTC"
            )

    def test_rejects_invalid_zone(self):
        with self.assertRaises(ValueError):
            selected_calendar_dates_utc(
                date(2026, 10, 1), date(2026, 10, 1), "Mars/Olympus"
            )


if __name__ == "__main__":
    unittest.main()
