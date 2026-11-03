# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Contract checks for ADR-0003 meter association support."""

import ast
from pathlib import Path
import unittest

API = (Path(__file__).resolve().parents[1] /
       'custom_components/energy_usage/api.py')


class MeterAssociationContractTests(unittest.TestCase):
    def test_import_requires_canonical_resource_ids(self):
        source = API.read_text()
        ast.parse(source)
        self.assertIn('resource_ids = result.get("resource_ids")', source)
        self.assertIn('len(set(resource_ids))', source)

    def test_association_uses_authenticated_backend_endpoint(self):
        source = API.read_text()
        self.assertIn('async def associate_resource(', source)
        self.assertIn('/v1/meters/{meter_id}/resources', source)
        self.assertIn('"resource_id": resource_id', source)
        self.assertIn('"already_associated"', source)
        self.assertIn('response.status == 409', source)


if __name__ == '__main__':
    unittest.main()
