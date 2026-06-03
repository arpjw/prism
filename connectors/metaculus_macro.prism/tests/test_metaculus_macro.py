"""Tests for the metaculus_macro connector."""
import asyncio
from pathlib import Path

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
    mod = _load_module("meta1")
    assert mod.MetaculusMacroConnector.metadata.slug == "metaculus_macro"


def test_metadata_transport_is_rest():
    mod = _load_module("meta2")
    assert mod.MetaculusMacroConnector.metadata.transport == "rest"


def test_no_auth_required():
    mod = _load_module("meta3")
    assert mod.MetaculusMacroConnector.metadata.auth_required is False


def test_health_check_false_initially():
    mod = _load_module("meta4")
    conn = mod.MetaculusMacroConnector()
    result = asyncio.get_event_loop().run_until_complete(conn.health_check())
    assert result is False


def test_extract_probability_from_community_prediction():
    mod = _load_module("meta5")
    conn = mod.MetaculusMacroConnector()
    data = {"community_prediction": {"full": {"q2": 0.35}}, "number_of_predictions": 100}
    prob = conn._extract_probability(data)
    assert abs(prob - 0.35) < 0.001


def test_extract_probability_fallback_to_prediction():
    mod = _load_module("meta6")
    conn = mod.MetaculusMacroConnector()
    data = {"prediction": 0.72}
    prob = conn._extract_probability(data)
    assert abs(prob - 0.72) < 0.001


def test_extract_probability_returns_none_for_empty():
    mod = _load_module("meta7")
    conn = mod.MetaculusMacroConnector()
    prob = conn._extract_probability({})
    assert prob is None
