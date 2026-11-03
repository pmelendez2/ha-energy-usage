# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Exercise authenticated XML import client without network access."""

import importlib.util
from pathlib import Path
import sys
import unittest

MODULE = (Path(__file__).resolve().parents[1] /
          'custom_components/energy_usage/api.py')
spec = importlib.util.spec_from_file_location('api_import_test', MODULE)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class Response:
    def __init__(self, status, payload):
        self.status = status
        self.payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    async def json(self, **_kwargs):
        return self.payload


class Session:
    def __init__(self, status=200, payload=None):
        self.status = status
        self.payload = payload
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return Response(self.status, self.payload)


class ImportTests(unittest.IsolatedAsyncioTestCase):
    async def test_import_request(self):
        result = {'observations': 2, 'unchanged': 1, 'accepted': 1, 'resource_ids': [13]}
        session = Session(payload=result)
        api = module.EnergyApi(session, 'https://example.test', 'token')
        self.assertEqual(await api.import_green_button(7, b'<xml/>'), result)
        url, kwargs = session.calls[0]
        self.assertEqual(url, 'https://example.test/v1/imports/'
                              'green-button?source_id=7')
        self.assertEqual(kwargs['data'], b'<xml/>')
        self.assertEqual(kwargs['headers']['Authorization'], 'Bearer token')

    async def test_invalid_inputs_do_not_send(self):
        session = Session()
        api = module.EnergyApi(session, 'https://example.test', 'token')
        for source, xml in [(0, b'x'), (True, b'x'), (1, b''),
                            (1, 'not bytes'), (1, b'x' * (8 * 1024 * 1024 + 1))]:
            with self.assertRaises(ValueError):
                await api.import_green_button(source, xml)
        self.assertEqual(session.calls, [])

    async def test_auth_failure_and_bad_response(self):
        for status in (401, 403):
            api = module.EnergyApi(Session(status=status),
                                   'https://example.test', 'token')
            with self.assertRaises(module.EnergyAuthError):
                await api.import_green_button(1, b'x')
        for payload in ({'observations': -1}, [], None):
            api = module.EnergyApi(Session(payload=payload),
                                   'https://example.test', 'token')
            with self.assertRaises(module.EnergyApiError):
                await api.import_green_button(1, b'x')
