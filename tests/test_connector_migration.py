"""Tests confirming all 5 built-in connectors are properly structured."""
import yaml
import pytest
from pathlib import Path

CONNECTORS_DIR = Path(__file__).parent.parent / "connectors"
EXPECTED_SLUGS = ["kalshi_fed", "polymarket_macro", "metaculus_macro", "manifold_macro", "fred_macro"]


@pytest.mark.parametrize("slug", EXPECTED_SLUGS)
def test_connector_directory_exists(slug):
    pkg = CONNECTORS_DIR / f"{slug}.prism"
    assert pkg.is_dir(), f"Missing connector directory: {pkg}"


@pytest.mark.parametrize("slug", EXPECTED_SLUGS)
def test_connector_has_manifest(slug):
    pkg = CONNECTORS_DIR / f"{slug}.prism"
    assert (pkg / "connector.prism").exists()
    assert (pkg / "__init__.py").exists()


@pytest.mark.parametrize("slug", EXPECTED_SLUGS)
def test_connector_metadata_matches_manifest(slug):
    pkg = CONNECTORS_DIR / f"{slug}.prism"
    manifest = yaml.safe_load((pkg / "connector.prism").read_text())
    assert manifest["slug"] == slug
    assert "version" in manifest
    assert manifest["prism_format_version"] == "1.0"


@pytest.mark.parametrize("slug", EXPECTED_SLUGS)
def test_connector_has_no_robinhood_imports(slug):
    pkg = CONNECTORS_DIR / f"{slug}.prism"
    init_text = (pkg / "__init__.py").read_text()
    assert "from robinhood" not in init_text
    assert "import robinhood" not in init_text
    assert "signals.kalshi" not in init_text
    assert "signals.polymarket" not in init_text


@pytest.mark.parametrize("slug", EXPECTED_SLUGS)
def test_connector_has_tests(slug):
    pkg = CONNECTORS_DIR / f"{slug}.prism"
    tests_dir = pkg / "tests"
    assert tests_dir.is_dir()
    test_files = list(tests_dir.glob("test_*.py"))
    assert len(test_files) >= 1, f"No test files in {tests_dir}"


@pytest.mark.parametrize("slug", EXPECTED_SLUGS)
def test_connector_has_readme(slug):
    pkg = CONNECTORS_DIR / f"{slug}.prism"
    assert (pkg / "README.md").exists()


@pytest.mark.parametrize("slug", EXPECTED_SLUGS)
def test_connector_has_schema(slug):
    pkg = CONNECTORS_DIR / f"{slug}.prism"
    import json
    schema_path = pkg / "schema.json"
    assert schema_path.exists()
    data = json.loads(schema_path.read_text())
    assert data.get("title") == "PricePoint"
