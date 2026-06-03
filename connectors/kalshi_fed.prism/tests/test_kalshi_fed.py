"""Tests for the kalshi_fed connector."""
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

CONNECTOR_DIR = Path(__file__).parent.parent


def test_manifest_exists():
    assert (CONNECTOR_DIR / "connector.prism").exists()


def test_init_exists():
    assert (CONNECTOR_DIR / "__init__.py").exists()


def test_readme_exists():
    assert (CONNECTOR_DIR / "README.md").exists()


def test_schema_exists():
    assert (CONNECTOR_DIR / "schema.json").exists()


def test_metadata_slug():
    from connectors.kalshi_fed.prism import KalshiFedConnector  # noqa: F401
    # Import via path instead
    import importlib.util, sys
    spec = importlib.util.spec_from_file_location("kalshi_fed", CONNECTOR_DIR / "__init__.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["kalshi_fed"] = mod
    spec.loader.exec_module(mod)
    assert mod.KalshiFedConnector.metadata.slug == "kalshi_fed"


def test_metadata_transport():
    import importlib.util, sys
    spec = importlib.util.spec_from_file_location("kalshi_fed2", CONNECTOR_DIR / "__init__.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["kalshi_fed2"] = mod
    spec.loader.exec_module(mod)
    assert mod.KalshiFedConnector.metadata.transport == "websocket"


def test_has_required_methods():
    import importlib.util, sys
    spec = importlib.util.spec_from_file_location("kalshi_fed3", CONNECTOR_DIR / "__init__.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["kalshi_fed3"] = mod
    spec.loader.exec_module(mod)
    cls = mod.KalshiFedConnector
    assert hasattr(cls, "start")
    assert hasattr(cls, "stop")
    assert hasattr(cls, "health_check")


def test_health_check_false_when_not_running():
    import importlib.util, sys
    spec = importlib.util.spec_from_file_location("kalshi_fed4", CONNECTOR_DIR / "__init__.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["kalshi_fed4"] = mod
    spec.loader.exec_module(mod)
    conn = mod.KalshiFedConnector()
    result = asyncio.get_event_loop().run_until_complete(conn.health_check())
    assert result is False


def test_handle_message_normalizes_price():
    import importlib.util, sys
    spec = importlib.util.spec_from_file_location("kalshi_fed5", CONNECTOR_DIR / "__init__.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["kalshi_fed5"] = mod
    spec.loader.exec_module(mod)
    received = []
    conn = mod.KalshiFedConnector(on_price=received.append)
    msg = {
        "type": "ticker",
        "yes_bid": "72",
        "volume": 1500,
        "market_ticker": "KXFED",
    }
    conn._handle_message(msg)
    assert len(received) == 1
    assert abs(received[0].price - 0.72) < 0.001
    assert received[0].source == "kalshi_fed"


def test_readme_documents_auth_fields():
    readme = (CONNECTOR_DIR / "README.md").read_text()
    assert "KALSHI_API_KEY" in readme
    assert "KALSHI_PRIVATE_KEY_PATH" in readme
