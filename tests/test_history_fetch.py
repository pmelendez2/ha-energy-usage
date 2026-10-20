# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Project Contributors
"""Test bounded history retrieval without a Home Assistant installation."""

import asyncio
from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from urllib.parse import parse_qs, urlsplit

BASE = Path(__file__).resolve().parents[1]
PKG = "energy_usage_window_test"
package = types.ModuleType(PKG)
package.__path__ = [str(BASE / "custom_components/energy_usage")]
sys.modules[PKG] = package
for name in ("api", "history", "history_fetch"):
    path = BASE / f"custom_components/energy_usage/{name}.py"
    spec = importlib.util.spec_from_file_location(f"{PKG}.{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

api_mod = sys.modules[f"{PKG}.api"]
fetch_mod = sys.modules[f"{PKG}.history_fetch"]
UTC = timezone.utc
START = datetime(2025, 1, 1, tzinfo=UTC)


class Response:
    """Simulate the aiohttp response context."""

    def __init__(self, payload, status=200):
        self.status = status
        self.payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    async def json(self, **_kwargs):
        return self.payload


class Session:
    """Return synthetic usage for the requested date range."""

    def __init__(self, observations=None, *, status=200):
        self.observations = observations or []
        self.requests = []
        self.status = status

    def get(self, url, **kwargs):
        self.requests.append((url, kwargs))
        path = urlsplit(url)
        meter_id = int(path.path.split("/")[3])
        query = parse_qs(path.query)
        begin = datetime.fromisoformat(
            query["start"][0].replace("Z", "+00:00")
        )
        end = datetime.fromisoformat(
            query["end"][0].replace("Z", "+00:00")
        )
        rows = [row for row in self.observations if
                begin <= datetime.fromisoformat(
                    row["start_utc"].replace("Z", "+00:00")
                ) < end]
        return Response({
            "physical_meter_id": meter_id,
            "resolved": True,
            "issues": [],
            "intervals": rows,
        }, self.status)


def sample(when, value=1000, unit=72, multiplier=0):
    """Produce one synthetic, utility-provided interval."""
    return {
        "start_utc": when.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_seconds": 3600,
        "raw_value": value,
        "unit_of_measure": unit,
        "power_of_ten_multiplier": multiplier,
        "accepted_revision_id": 3,
    }


class HistoryFetchTests(unittest.IsolatedAsyncioTestCase):
    """Exercise the authenticated window-to-normalization pipeline."""

    async def test_gap_remains_missing_across_windows(self):
        rows = [sample(START), sample(START + timedelta(days=40))]
        session = Session(rows)
        api = api_mod.EnergyApi(session, "https://example.test", "token")
        actual = await fetch_mod.fetch_usage_history(
            api, 1, 1, START, START + timedelta(days=63)
        )
        self.assertEqual(len(actual), 2)
        self.assertEqual(len(session.requests), 3)
        self.assertEqual([x.value for x in actual], [1, 1])
        self.assertTrue(all("Bearer token" in str(options["headers"])
                            for _, options in session.requests))

    async def test_window_end_exclusive(self):
        rows = [sample(START + timedelta(days=31))]
        session = Session(rows)
        api = api_mod.EnergyApi(session, "https://example.test", "token")
        actual = await fetch_mod.fetch_usage_history(
            api, 1, 1, START, START + timedelta(days=31)
        )
        self.assertEqual(actual, [])

    async def test_gas_units(self):
        session = Session([sample(START, 2500, 169, -3)])
        api = api_mod.EnergyApi(session, "https://example.test", "token")
        rows = await fetch_mod.fetch_usage_history(
            api, 2, 7, START, START + timedelta(days=1)
        )
        self.assertEqual(rows[0].unit, "therm")
        self.assertEqual(str(rows[0].value), "2.500")

    async def test_bad_window_parameter_rejected_locally(self):
        api = api_mod.EnergyApi(Session(), "https://example.test", "token")
        with self.assertRaises(ValueError):
            await api.window(1, START, START + timedelta(days=32))
        with self.assertRaises(ValueError):
            await api.window(1, START, START)

    async def test_backend_error_never_returns_partial_history(self):
        api = api_mod.EnergyApi(
            Session([sample(START)], status=409),
            "https://example.test", "token"
        )
        with self.assertRaises(api_mod.EnergyApiError):
            await fetch_mod.fetch_usage_history(
                api, 1, 1, START, START + timedelta(days=40)
            )

    async def test_invalid_units_rejected(self):
        api = api_mod.EnergyApi(
            Session([sample(START, unit=169)]),
            "https://example.test", "token"
        )
        with self.assertRaises(ValueError):
            await fetch_mod.fetch_usage_history(
                api, 1, 1, START, START + timedelta(days=1)
            )

    async def test_invalid_meter_response_rejected(self):
        class WrongMeter(Session):
            def get(self, url, **kwargs):
                return Response({
                    "physical_meter_id": 99,
                    "resolved": True,
                    "issues": [],
                    "intervals": [],
                })
        api = api_mod.EnergyApi(
            WrongMeter(), "https://example.test", "token"
        )
        with self.assertRaises(api_mod.EnergyApiError):
            await fetch_mod.fetch_usage_history(
                api, 1, 1, START, START + timedelta(days=1)
            )


if __name__ == "__main__":
    unittest.main()
