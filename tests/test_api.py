# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Project Contributors
"""Exercise API response, authentication, and URL boundaries."""

import asyncio
import importlib.util
from pathlib import Path
import sys
import unittest

MODULE = (
    Path(__file__).resolve().parents[1]
    / "custom_components/energy_usage/api.py"
)
spec = importlib.util.spec_from_file_location("energy_usage_api_test", MODULE)
api_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = api_module
spec.loader.exec_module(api_module)


class FakeResponse:
    """A minimal aiohttp-compatible response context."""

    def __init__(self, status, payload):
        self.status = status
        self.payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    async def json(self, **_kwargs):
        return self.payload


class FakeSession:
    """Capture outgoing requests without a network connection."""

    def __init__(self, status=200, payload=None):
        self.status = status
        self.payload = payload
        self.requests = []

    def get(self, url, **kwargs):
        self.requests.append((url, kwargs))
        return FakeResponse(self.status, self.payload)


class EnergyApiTests(unittest.IsolatedAsyncioTestCase):
    """Check the read-only HTTP client contract."""

    async def test_meters_and_bearer_token(self):
        session = FakeSession(payload=[{"id": 1}])
        client = api_module.EnergyApi(
            session, "http://localhost:8080/", "secret"
        )
        self.assertEqual(await client.meters(), [{"id": 1}])
        url, options = session.requests[0]
        self.assertEqual(url, "http://localhost:8080/v1/meters")
        self.assertEqual(
            options["headers"], {"Authorization": "Bearer secret"}
        )

    async def test_stream_request(self):
        session = FakeSession(payload={"status": "ok"})
        client = api_module.EnergyApi(
            session, "https://example.test:8080", "secret"
        )
        self.assertEqual(
            await client.stream(4), {"status": "ok"}
        )
        self.assertTrue(
            session.requests[0][0].endswith("/v1/meters/4/stream")
        )

    async def test_authentication_failures(self):
        for status in (401, 403):
            with self.subTest(status=status):
                client = api_module.EnergyApi(
                    FakeSession(status=status),
                    "https://example.test", "secret"
                )
                with self.assertRaises(api_module.EnergyAuthError):
                    await client.meters()

    async def test_http_and_schema_errors(self):
        client = api_module.EnergyApi(
            FakeSession(status=500), "https://example.test", "secret"
        )
        with self.assertRaises(api_module.EnergyApiError):
            await client.meters()
        client = api_module.EnergyApi(
            FakeSession(payload={"not": "a list"}),
            "https://example.test", "secret"
        )
        with self.assertRaises(api_module.EnergyApiError):
            await client.meters()

    async def test_reject_url_credentials_and_paths(self):
        for url in (
            "ftp://example.test", "http://user@example.test",
            "https://example.test/path", "https://example.test/?x=1",
            "https://example.test/#frag", "http:///no-host",
        ):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    api_module.EnergyApi(FakeSession(), url, "secret")
