"""Tests for registry.json and RegistryClient."""
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

REGISTRY_PATH = Path(__file__).parent.parent / "registry" / "registry.json"
SCHEMA_PATH = Path(__file__).parent.parent / "registry" / "schema.json"
REQUIRED_SLUGS = {"kalshi_fed", "polymarket_macro", "metaculus_macro", "manifold_macro", "fred_macro"}


def test_registry_json_is_valid_json():
    data = json.loads(REGISTRY_PATH.read_text())
    assert isinstance(data, dict)


def test_registry_json_passes_schema():
    jsonschema = pytest.importorskip("jsonschema")
    registry = json.loads(REGISTRY_PATH.read_text())
    schema = json.loads(SCHEMA_PATH.read_text())
    jsonschema.validate(registry, schema)


def test_all_five_connectors_present():
    registry = json.loads(REGISTRY_PATH.read_text())
    slugs = {c["slug"] for c in registry["connectors"]}
    assert REQUIRED_SLUGS.issubset(slugs)


def test_slugs_are_unique():
    registry = json.loads(REGISTRY_PATH.read_text())
    slugs = [c["slug"] for c in registry["connectors"]]
    assert len(slugs) == len(set(slugs))


def test_source_urls_are_well_formed():
    registry = json.loads(REGISTRY_PATH.read_text())
    for connector in registry["connectors"]:
        url = connector.get("source_url", "")
        assert url.startswith("https://"), f"Bad URL for {connector['slug']}: {url!r}"


def test_registry_client_fetch_returns_parsed(tmp_path):
    from prism.registry_client import RegistryClient
    sample = {"version": "1.0", "updated_at": "2026-01-01T00:00:00Z", "connectors": []}
    cache_file = tmp_path / "cache.json"
    with patch("httpx.get") as mock_get, \
         patch("prism.registry_client.CACHE_FILE", cache_file), \
         patch("prism.registry_client.CACHE_DIR", tmp_path):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = sample
        mock_get.return_value = mock_resp
        client = RegistryClient()
        result = client.fetch()
    assert result["version"] == "1.0"


def test_registry_client_find_by_slug():
    from prism.registry_client import RegistryClient
    sample = {
        "version": "1.0", "updated_at": "2026-01-01T00:00:00Z",
        "connectors": [{"slug": "kalshi_fed", "name": "Kalshi Fed"}],
    }
    with patch.object(RegistryClient, "fetch", return_value=sample):
        result = RegistryClient().find("kalshi_fed")
    assert result["name"] == "Kalshi Fed"


def test_registry_client_find_returns_none_for_unknown():
    from prism.registry_client import RegistryClient
    sample = {"version": "1.0", "updated_at": "2026-01-01T00:00:00Z", "connectors": []}
    with patch.object(RegistryClient, "fetch", return_value=sample):
        assert RegistryClient().find("nonexistent") is None


def test_registry_client_search_filters_by_tag():
    from prism.registry_client import RegistryClient
    sample = {
        "version": "1.0", "updated_at": "2026-01-01T00:00:00Z",
        "connectors": [
            {"slug": "a", "tags": ["fed", "rates"]},
            {"slug": "b", "tags": ["macro"]},
        ],
    }
    with patch.object(RegistryClient, "fetch", return_value=sample):
        result = RegistryClient().search(tags=["fed"])
    assert len(result) == 1
    assert result[0]["slug"] == "a"


def test_registry_client_writes_cache(tmp_path):
    from prism.registry_client import RegistryClient
    sample = {"version": "1.0", "updated_at": "2026-01-01T00:00:00Z", "connectors": []}
    cache_file = tmp_path / "registry_cache.json"
    with patch("httpx.get") as mock_get, \
         patch("prism.registry_client.CACHE_FILE", cache_file), \
         patch("prism.registry_client.CACHE_DIR", tmp_path):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = sample
        mock_get.return_value = mock_resp
        RegistryClient().fetch()
    assert cache_file.exists()
    cached = json.loads(cache_file.read_text())
    assert "timestamp" in cached
    assert cached["data"]["version"] == "1.0"


def test_registry_client_uses_cache_on_network_failure(tmp_path):
    from prism.registry_client import RegistryClient
    sample = {"version": "1.0", "updated_at": "2026-01-01T00:00:00Z", "connectors": [{"slug": "cached"}]}
    cache_file = tmp_path / "registry_cache.json"
    cache_file.write_text(json.dumps({"timestamp": time.time(), "data": sample}))
    with patch("httpx.get", side_effect=Exception("network down")), \
         patch("prism.registry_client.CACHE_FILE", cache_file), \
         patch("prism.registry_client.CACHE_DIR", tmp_path):
        result = RegistryClient().fetch()
    assert result["connectors"][0]["slug"] == "cached"
