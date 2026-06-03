"""Tests for prism.base module."""
import pytest
import yaml
from datetime import datetime, timezone
from pathlib import Path

from prism.base import (
    PricePoint, PrismMetadata, PrismRegistry, PrismConnector,
    validate_manifest,
)

UTC = timezone.utc


def make_ts():
    return datetime(2026, 1, 1, tzinfo=UTC)


# --- PricePoint ---

def test_pricepoint_rejects_price_above_one():
    with pytest.raises(ValueError, match="price must be in"):
        PricePoint(timestamp=make_ts(), price=1.01)


def test_pricepoint_rejects_price_below_zero():
    with pytest.raises(ValueError, match="price must be in"):
        PricePoint(timestamp=make_ts(), price=-0.01)


def test_pricepoint_accepts_zero():
    pt = PricePoint(timestamp=make_ts(), price=0.0)
    assert pt.price == 0.0


def test_pricepoint_accepts_one():
    pt = PricePoint(timestamp=make_ts(), price=1.0)
    assert pt.price == 1.0


def test_pricepoint_accepts_midrange():
    pt = PricePoint(timestamp=make_ts(), price=0.5, volume=100, slug="TEST", source="test_conn")
    assert pt.price == 0.5
    assert pt.volume == 100
    assert pt.slug == "TEST"
    assert pt.source == "test_conn"


# --- PrismMetadata ---

def test_prism_metadata_new_fields():
    m = PrismMetadata(
        name="Test", slug="test", version="1.0.0", author="alice",
        source_type="prediction_market", transport="rest",
        description="A test", auth_required=False,
        homepage="https://example.com", tags=["foo", "bar"],
    )
    assert m.homepage == "https://example.com"
    assert m.tags == ["foo", "bar"]
    assert m.auth_fields == []
    assert m.contract_slugs == []


# --- PrismRegistry helpers ---

def _make_valid_pkg(tmp_path: Path, slug: str = "test_conn") -> Path:
    pkg = tmp_path / f"{slug}.prism"
    pkg.mkdir()
    manifest = {
        "prism_format_version": "1.0",
        "name": "Test Connector", "slug": slug,
        "version": "1.0.0", "author": "alice",
        "source_type": "prediction_market", "transport": "rest",
        "description": "desc", "auth_required": False,
        "auth_fields": [], "contract_slugs": ["TEST"],
    }
    (pkg / "connector.prism").write_text(yaml.dump(manifest))
    (pkg / "__init__.py").write_text(f"""
from prism.base import PrismConnector, PrismMetadata

class TestConnector(PrismConnector):
    metadata = PrismMetadata(
        name="Test Connector", slug="{slug}", version="1.0.0",
        author="alice", source_type="prediction_market", transport="rest",
        description="desc", auth_required=False,
    )
    async def start(self): pass
    async def stop(self): pass
    async def health_check(self): return True
""")
    return pkg


# --- PrismRegistry ---

def test_registry_load_directory_valid(tmp_path):
    _make_valid_pkg(tmp_path, "test_conn")
    reg = PrismRegistry()
    reg.load_directory(tmp_path)
    assert reg.get("test_conn") is not None


def test_registry_load_directory_skips_missing_manifest(tmp_path):
    bad = tmp_path / "bad.prism"
    bad.mkdir()
    (bad / "__init__.py").write_text("x = 1")
    # no connector.prism
    reg = PrismRegistry()
    reg.load_directory(tmp_path)
    assert reg.get("bad") is None


def test_registry_load_directory_skips_malformed_init(tmp_path):
    pkg = tmp_path / "broken.prism"
    pkg.mkdir()
    manifest = {
        "prism_format_version": "1.0", "name": "Broken", "slug": "broken",
        "version": "1.0.0", "author": "a", "source_type": "custom",
        "transport": "rest", "description": "d", "auth_required": False,
        "contract_slugs": ["X"],
    }
    (pkg / "connector.prism").write_text(yaml.dump(manifest))
    (pkg / "__init__.py").write_text("raise RuntimeError('boom')")
    reg = PrismRegistry()
    reg.load_directory(tmp_path)  # should warn and skip
    assert reg.get("broken") is None


def test_registry_summary_structure(tmp_path):
    _make_valid_pkg(tmp_path, "summary_conn")
    reg = PrismRegistry()
    reg.load_directory(tmp_path)
    summary = reg.summary()
    assert len(summary) >= 1
    item = summary[0]
    for key in ("name", "slug", "version", "transport", "auth_required", "status"):
        assert key in item


def test_registry_get_returns_none_for_unknown(tmp_path):
    reg = PrismRegistry()
    assert reg.get("nonexistent") is None


# --- validate_manifest ---

def _write_manifest(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "connector.prism"
    p.write_text(yaml.dump(data))
    return p


def test_validate_manifest_passes_valid(tmp_path):
    data = {
        "prism_format_version": "1.0",
        "name": "Test", "slug": "test", "version": "1.0.0",
        "author": "alice", "source_type": "prediction_market",
        "transport": "rest", "description": "desc",
        "auth_required": False, "contract_slugs": ["X"],
    }
    result = validate_manifest(_write_manifest(tmp_path, data))
    assert result["slug"] == "test"


def test_validate_manifest_raises_on_missing_field(tmp_path):
    data = {
        "prism_format_version": "1.0",
        "name": "Test", "slug": "test", "version": "1.0.0",
        # missing: author, source_type, transport, description, auth_required, contract_slugs
    }
    with pytest.raises(ValueError, match="Missing required field"):
        validate_manifest(_write_manifest(tmp_path, data))


def test_validate_manifest_raises_on_wrong_type(tmp_path):
    data = {
        "prism_format_version": "1.0",
        "name": "Test", "slug": "test", "version": "1.0.0",
        "author": "alice", "source_type": "prediction_market",
        "transport": "rest", "description": "desc",
        "auth_required": "not-a-bool",
        "contract_slugs": ["X"],
    }
    with pytest.raises(ValueError, match="must be bool"):
        validate_manifest(_write_manifest(tmp_path, data))


def test_validate_manifest_raises_on_wrong_format_version(tmp_path):
    data = {
        "prism_format_version": "2.0",
        "name": "Test", "slug": "test", "version": "1.0.0",
        "author": "alice", "source_type": "prediction_market",
        "transport": "rest", "description": "desc",
        "auth_required": False, "contract_slugs": ["X"],
    }
    with pytest.raises(ValueError, match="prism_format_version"):
        validate_manifest(_write_manifest(tmp_path, data))


def test_validate_manifest_raises_on_missing_file(tmp_path):
    with pytest.raises(ValueError, match="not found"):
        validate_manifest(tmp_path / "nonexistent.prism")
