"""Tests for the polymarket_macro connector."""
import asyncio
from pathlib import Path

import pytest

CONNECTOR_DIR = Path(__file__).parent.parent


def _load_module(key):
    import importlib.util, sys
    spec = importlib.util.spec_from_file_location(key, CONNECTOR_DIR / "__init__.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


def test_manifest_exists():
    assert (CONNECTOR_DIR / "connector.prism").exists()


def test_init_exists():
    assert (CONNECTOR_DIR / "__init__.py").exists()


def test_readme_exists():
    assert (CONNECTOR_DIR / "README.md").exists()


def test_schema_exists():
    assert (CONNECTOR_DIR / "schema.json").exists()


def test_metadata_slug():
    mod = _load_module("poly1")
    assert mod.PolymarketMacroConnector.metadata.slug == "polymarket_macro"


def test_metadata_no_auth_required():
    mod = _load_module("poly2")
    assert mod.PolymarketMacroConnector.metadata.auth_required is False


def test_has_required_methods():
    mod = _load_module("poly3")
    cls = mod.PolymarketMacroConnector
    assert hasattr(cls, "start") and hasattr(cls, "stop") and hasattr(cls, "health_check")


def test_health_check_false_when_not_running():
    mod = _load_module("poly4")
    conn = mod.PolymarketMacroConnector()
    result = asyncio.get_event_loop().run_until_complete(conn.health_check())
    assert result is False


def test_handle_message_emits_price_point():
    mod = _load_module("poly5")
    received = []
    conn = mod.PolymarketMacroConnector(on_price=received.append)
    msg = {
        "event_type": "price_change",
        "market": "will-the-fed-cut-rates-in-2026",
        "price": "0.68",
        "size": 500,
    }
    conn._handle_message(msg)
    assert len(received) == 1
    assert abs(received[0].price - 0.68) < 0.001
    assert received[0].source == "polymarket_macro"


def test_handle_message_clamps_price():
    mod = _load_module("poly6")
    received = []
    conn = mod.PolymarketMacroConnector(on_price=received.append)
    msg = {"event_type": "price_change", "market": "test", "price": "1.5", "size": 0}
    conn._handle_message(msg)
    assert len(received) == 1
    assert received[0].price == 1.0
