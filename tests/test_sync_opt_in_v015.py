"""v0.1.5 automatic synchronization opt-in regression."""
import importlib.util
from pathlib import Path
import unittest
from types import SimpleNamespace

MODULE = Path(__file__).resolve().parents[1] / (
    "custom_components/energy_usage/statistics_sync_settings.py"
)
spec = importlib.util.spec_from_file_location("sync_settings_v015", MODULE)
settings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(settings)


class SyncOptInTests(unittest.TestCase):
    def test_new_and_legacy_entries_disabled(self):
        for options in ({}, {"sync_interval_hours": 6,
                             "sync_on_startup": True}):
            self.assertFalse(settings.sync_preferences(
                SimpleNamespace(options=options))[0])

    def test_explicit_opt_in(self):
        entry = SimpleNamespace(options={
            "sync_enabled": True, "sync_interval_hours": 12,
            "sync_on_startup": False,
        })
        self.assertEqual(settings.sync_preferences(entry),
                         (True, 12, False))

    def test_reject_invalid_enable_value(self):
        with self.assertRaises(ValueError):
            settings.sync_preferences(SimpleNamespace(
                options={"sync_enabled": "true"}))
