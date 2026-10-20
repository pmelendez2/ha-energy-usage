# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Project Contributors
"""Static contract tests for configuration-flow requirements."""

import ast
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components/energy_usage"


class ConfigFlowContractTest(unittest.TestCase):
    """Check features without initializing Home Assistant."""

    @classmethod
    def setUpClass(cls):
        """Parse the integration source and translation resources."""
        cls.tree = ast.parse(
            (INTEGRATION / "config_flow.py").read_text()
        )
        cls.strings = json.loads(
            (INTEGRATION / "strings.json").read_text()
        )

    def test_has_native_config_steps(self):
        """Installation, recovery and host changes have UI steps."""
        methods = {
            node.name
            for node in ast.walk(self.tree)
            if isinstance(node, ast.AsyncFunctionDef)
        }
        self.assertTrue({
            "async_step_user",
            "async_step_reauth",
            "async_step_reauth_confirm",
            "async_step_reconfigure",
        } <= methods)

    def test_reconfigure_and_reauth_descriptions(self):
        """Both recovery flows have customer-facing labels."""
        steps = self.strings["config"]["step"]
        self.assertIn("url", steps["reconfigure"]["data"])
        self.assertIn("api_token", steps["reauth_confirm"]["data"])

    def test_translation_json(self):
        """All advertised success messages are represented."""
        aborts = self.strings["config"]["abort"]
        self.assertIn("reconfigure_successful", aborts)
        self.assertIn("reauth_successful", aborts)


if __name__ == "__main__":
    unittest.main()
