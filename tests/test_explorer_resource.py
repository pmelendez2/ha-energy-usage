# SPDX-License-Identifier: MIT
"""Test bundled Explorer registration."""

import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock


COMPONENT = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "energy_usage"
)
INIT_FILE = COMPONENT / "__init__.py"
EXPLORER_FILE = COMPONENT / "www" / "energy-usage-explorer.js"
EXPLORER_URL = "/energy-usage/energy-usage-explorer.js"
LEGACY_EXPLORER_URL = "/energy_usage/energy-usage-explorer.js"
UTILITY_CARD_URL = "/energy-usage/energy-usage-utility-card.js"


class StaticPathConfig:
    """Minimal Home Assistant static-path test substitute."""

    def __init__(self, url_path, path, cache_headers):
        self.url_path = url_path
        self.path = path
        self.cache_headers = cache_headers


def load_setup_functions():
    """Load the actual setup functions without importing HA."""
    source = INIT_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source)

    selected = [
        node
        for node in tree.body
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name in (
            "async_setup",
            "async_register_explorer",
        )
    ]

    assert len(selected) == 2

    module = ast.Module(body=selected, type_ignores=[])
    ast.fix_missing_locations(module)

    namespace = {
        "__file__": str(INIT_FILE),
        "Path": Path,
        "StaticPathConfig": StaticPathConfig,
        "EXPLORER_URL": EXPLORER_URL,
        "LEGACY_EXPLORER_URL": LEGACY_EXPLORER_URL,
        "UTILITY_CARD_URL": UTILITY_CARD_URL,
    }

    exec(compile(module, str(INIT_FILE), "exec"), namespace)
    return namespace


def test_bundled_explorer_exists():
    assert EXPLORER_FILE.is_file()

    source = EXPLORER_FILE.read_text(encoding="utf-8")
    assert "Use latest available" in source
    assert "Jump to day" in source
    assert "selected data point" in source


def test_explorer_static_registration():
    namespace = load_setup_functions()
    register = AsyncMock()

    hass = SimpleNamespace(
        http=SimpleNamespace(
            async_register_static_paths=register,
        ),
    )

    asyncio.run(namespace["async_register_explorer"](hass))
    register.assert_awaited_once()

    paths = register.await_args.args[0]
    assert len(paths) == 3
    assert [path.url_path for path in paths] == [
        EXPLORER_URL, LEGACY_EXPLORER_URL, UTILITY_CARD_URL
    ]
    for path in paths[:2]:
        assert Path(path.path).resolve() == EXPLORER_FILE.resolve()
        assert path.cache_headers is False
    assert Path(paths[2].path).name == "energy-usage-utility-card.js"
