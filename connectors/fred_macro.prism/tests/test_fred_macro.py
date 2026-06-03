"""Tests for the fred_macro connector."""
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


def test_readme_documents_fred_api_key():
    readme = (CONNECTOR_DIR / "README.md").read_text()
    assert "FRED_API_KEY" in readme


def test_metadata_slug():
    mod = _load_module("fred1")
    assert mod.FredMacroConnector.metadata.slug == "fred_macro"


def test_metadata_source_type():
    mod = _load_module("fred2")
    assert mod.FredMacroConnector.metadata.source_type == "alternative_data"


def test_auth_required():
    mod = _load_module("fred3")
    assert mod.FredMacroConnector.metadata.auth_required is True
    assert "FRED_API_KEY" in mod.FredMacroConnector.metadata.auth_fields


def test_health_check_false_initially():
    mod = _load_module("fred4")
    conn = mod.FredMacroConnector()
    result = asyncio.get_event_loop().run_until_complete(conn.health_check())
    assert result is False


def test_series_bounds_cover_all_contract_slugs():
    mod = _load_module("fred5")
    for slug in mod.FredMacroConnector.metadata.contract_slugs:
        assert slug in mod.SERIES_BOUNDS, f"{slug} missing from SERIES_BOUNDS"


def test_normalization_at_midrange():
    mod = _load_module("fred6")
    # 5.0% → 0.5 for a [0, 10] range
    min_val, max_val = mod.SERIES_BOUNDS["FEDFUNDS"]
    price = (5.0 - min_val) / (max_val - min_val)
    assert abs(price - 0.5) < 0.001
