"""Tests for the manifold_macro connector."""
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
    mod = _load_module("mani1")
    assert mod.ManifoldMacroConnector.metadata.slug == "manifold_macro"


def test_metadata_transport_rest():
    mod = _load_module("mani2")
    assert mod.ManifoldMacroConnector.metadata.transport == "rest"


def test_no_auth_required():
    mod = _load_module("mani3")
    assert mod.ManifoldMacroConnector.metadata.auth_required is False


def test_health_check_false_initially():
    mod = _load_module("mani4")
    conn = mod.ManifoldMacroConnector()
    result = asyncio.get_event_loop().run_until_complete(conn.health_check())
    assert result is False


def test_contract_slugs_not_empty():
    mod = _load_module("mani5")
    assert len(mod.ManifoldMacroConnector.metadata.contract_slugs) > 0


def test_has_all_abstract_methods():
    mod = _load_module("mani6")
    cls = mod.ManifoldMacroConnector
    assert hasattr(cls, "start")
    assert hasattr(cls, "stop")
    assert hasattr(cls, "health_check")
    assert hasattr(cls, "_poll_loop")
    assert hasattr(cls, "_fetch_all")
