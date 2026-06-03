"""Tests for prism CLI commands."""
import json
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from prism.cli import app

runner = CliRunner()

SAMPLE_REGISTRY = {
    "version": "1.0",
    "updated_at": "2026-06-02T00:00:00Z",
    "connectors": [
        {
            "name": "Kalshi Fed Markets",
            "slug": "kalshi_fed",
            "version": "1.0.0",
            "author": "arpjw",
            "source_type": "prediction_market",
            "transport": "websocket",
            "description": "Streams KXFED contract prices.",
            "auth_required": True,
            "auth_fields": ["KALSHI_API_KEY"],
            "contract_slugs": ["KXFED"],
            "tags": ["fed", "rates"],
            "verified": True,
            "source_url": "https://example.com/archive.tar.gz",
            "source_path": "connectors/kalshi_fed.prism",
        },
        {
            "name": "FRED Macro",
            "slug": "fred_macro",
            "version": "1.0.0",
            "author": "arpjw",
            "source_type": "alternative_data",
            "transport": "rest",
            "description": "Polls FRED series.",
            "auth_required": True,
            "auth_fields": ["FRED_API_KEY"],
            "contract_slugs": ["FEDFUNDS"],
            "tags": ["fed", "macro", "economic-data"],
            "verified": True,
            "source_url": "https://example.com/archive.tar.gz",
            "source_path": "connectors/fred_macro.prism",
        },
    ],
}


def _make_valid_pkg(base: Path, slug: str = "test_conn") -> Path:
    pkg = base / f"{slug}.prism"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "tests").mkdir(exist_ok=True)
    manifest = {
        "prism_format_version": "1.0",
        "name": "Test Connector", "slug": slug, "version": "1.0.0",
        "author": "alice", "source_type": "prediction_market", "transport": "rest",
        "description": "A test connector", "auth_required": False,
        "auth_fields": [], "contract_slugs": ["TEST_SLUG"],
    }
    (pkg / "connector.prism").write_text(yaml.dump(manifest))
    (pkg / "__init__.py").write_text(f"""
from prism.base import PrismConnector, PrismMetadata

class TestConnector(PrismConnector):
    metadata = PrismMetadata(
        name="Test Connector", slug="{slug}", version="1.0.0",
        author="alice", source_type="prediction_market", transport="rest",
        description="A test connector", auth_required=False,
    )
    async def start(self): pass
    async def stop(self): pass
    async def health_check(self): return True
""")
    (pkg / "tests" / f"test_{slug}.py").write_text("def test_placeholder(): pass\n")
    return pkg


# --- scaffold ---

def test_scaffold_creates_directory_structure(tmp_path):
    result = runner.invoke(app, [
        "scaffold", "--name", "My Source", "--slug", "my_source",
        "--type", "prediction_market", "--transport", "rest",
        "--output-dir", str(tmp_path),
    ])
    assert result.exit_code == 0
    pkg = tmp_path / "my_source.prism"
    assert pkg.is_dir()
    assert (pkg / "connector.prism").exists()
    assert (pkg / "__init__.py").exists()
    assert (pkg / "schema.json").exists()
    assert (pkg / "README.md").exists()
    assert (pkg / "tests" / "test_my_source.py").exists()


def test_scaffold_with_author_sets_manifest(tmp_path):
    runner.invoke(app, [
        "scaffold", "--name", "My Source", "--slug", "my_source",
        "--type", "custom", "--transport", "rest",
        "--output-dir", str(tmp_path), "--author", "testauthor",
    ])
    manifest = yaml.safe_load((tmp_path / "my_source.prism" / "connector.prism").read_text())
    assert manifest["author"] == "testauthor"


def test_scaffold_manifest_has_correct_slug(tmp_path):
    runner.invoke(app, [
        "scaffold", "--name", "Foo Bar", "--slug", "foo_bar",
        "--type", "news", "--transport", "push",
        "--output-dir", str(tmp_path), "--author", "alice",
    ])
    manifest = yaml.safe_load((tmp_path / "foo_bar.prism" / "connector.prism").read_text())
    assert manifest["slug"] == "foo_bar"
    assert manifest["transport"] == "push"


# --- validate ---

def test_validate_passes_valid_package(tmp_path):
    pkg = _make_valid_pkg(tmp_path)
    result = runner.invoke(app, ["validate", str(pkg)])
    assert result.exit_code == 0


def test_validate_fails_missing_manifest(tmp_path):
    pkg = tmp_path / "empty.prism"
    pkg.mkdir()
    result = runner.invoke(app, ["validate", str(pkg)])
    assert result.exit_code == 1


def test_validate_fails_missing_subclass(tmp_path):
    pkg = tmp_path / "no_class.prism"
    pkg.mkdir()
    manifest = {
        "prism_format_version": "1.0", "name": "Bad", "slug": "bad", "version": "1.0.0",
        "author": "a", "source_type": "custom", "transport": "rest",
        "description": "d", "auth_required": False, "contract_slugs": ["X"],
    }
    (pkg / "connector.prism").write_text(yaml.dump(manifest))
    (pkg / "__init__.py").write_text("x = 1\n")
    result = runner.invoke(app, ["validate", str(pkg)])
    assert result.exit_code == 1


def test_validate_warns_missing_tests(tmp_path):
    pkg = tmp_path / "no_tests.prism"
    pkg.mkdir()
    manifest = {
        "prism_format_version": "1.0", "name": "T", "slug": "no_tests", "version": "1.0.0",
        "author": "a", "source_type": "custom", "transport": "rest",
        "description": "d", "auth_required": False, "contract_slugs": ["X"],
    }
    (pkg / "connector.prism").write_text(yaml.dump(manifest))
    (pkg / "__init__.py").write_text("""
from prism.base import PrismConnector, PrismMetadata
class NoTestsConnector(PrismConnector):
    metadata = PrismMetadata(
        name="T", slug="no_tests", version="1.0.0", author="a",
        source_type="custom", transport="rest", description="d", auth_required=False,
    )
    async def start(self): pass
    async def stop(self): pass
    async def health_check(self): return True
""")
    result = runner.invoke(app, ["validate", str(pkg)])
    assert result.exit_code == 0
    assert "WARN" in result.output


def test_validate_warns_undocumented_auth_field(tmp_path):
    pkg = tmp_path / "auth_warn.prism"
    pkg.mkdir()
    manifest = {
        "prism_format_version": "1.0", "name": "Auth", "slug": "auth_warn", "version": "1.0.0",
        "author": "a", "source_type": "custom", "transport": "rest",
        "description": "d", "auth_required": True,
        "auth_fields": ["MY_SECRET_KEY"], "contract_slugs": ["X"],
    }
    (pkg / "connector.prism").write_text(yaml.dump(manifest))
    (pkg / "__init__.py").write_text("""
from prism.base import PrismConnector, PrismMetadata
class AuthWarnConnector(PrismConnector):
    metadata = PrismMetadata(
        name="Auth", slug="auth_warn", version="1.0.0", author="a",
        source_type="custom", transport="rest", description="d", auth_required=True,
        auth_fields=["MY_SECRET_KEY"],
    )
    async def start(self): pass
    async def stop(self): pass
    async def health_check(self): return True
""")
    (pkg / "README.md").write_text("# Auth Test\nNo mention of the key here.")
    result = runner.invoke(app, ["validate", str(pkg)])
    assert result.exit_code == 0
    assert "WARN" in result.output


# --- list ---

def test_list_installed_reads_connectors_dir(tmp_path):
    import os
    connectors_dir = tmp_path / "connectors"
    connectors_dir.mkdir()
    _make_valid_pkg(connectors_dir, "local_conn")
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = runner.invoke(app, ["list", "--installed"])
    finally:
        os.chdir(old_cwd)
    assert result.exit_code == 0
    assert "local_conn" in result.output


def test_list_registry_fetches_and_displays():
    with patch("prism.registry_client.RegistryClient.fetch", return_value=SAMPLE_REGISTRY):
        result = runner.invoke(app, ["list", "--registry"])
    assert result.exit_code == 0
    assert "kalshi_fed" in result.output
    assert "fred_macro" in result.output


def test_list_tags_filters_correctly():
    with patch("prism.registry_client.RegistryClient.fetch", return_value=SAMPLE_REGISTRY):
        result = runner.invoke(app, ["list", "--registry", "--tags", "economic-data"])
    assert result.exit_code == 0
    assert "fred_macro" in result.output
    assert "kalshi_fed" not in result.output


# --- install ---

def test_install_force_calls_with_force(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    with patch("prism.installer.install_connector") as mock_install:
        mock_install.return_value = output_dir / "kalshi_fed.prism"
        runner.invoke(app, ["install", "kalshi_fed", "--output-dir", str(output_dir), "--force"])
    mock_install.assert_called_once()
    call_kwargs = mock_install.call_args
    assert call_kwargs.kwargs.get("force") is True or (
        len(call_kwargs.args) >= 4 and call_kwargs.args[3] is True
    )


def test_install_aborts_on_not_found(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    with patch("prism.registry_client.RegistryClient.fetch", return_value={
        "version": "1.0", "updated_at": "2026-01-01T00:00:00Z", "connectors": []
    }):
        result = runner.invoke(app, ["install", "nonexistent_slug", "--output-dir", str(output_dir)])
    assert result.exit_code != 0


def test_install_aborts_when_already_exists(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "kalshi_fed.prism").mkdir()
    with patch("prism.installer.install_connector", side_effect=FileExistsError("already exists")):
        result = runner.invoke(app, ["install", "kalshi_fed", "--output-dir", str(output_dir)])
    assert result.exit_code != 0
    assert "Error" in result.output


# --- info ---

def test_info_shows_connector_details():
    with patch("prism.registry_client.RegistryClient.fetch", return_value=SAMPLE_REGISTRY):
        result = runner.invoke(app, ["info", "kalshi_fed"])
    assert result.exit_code == 0
    assert "Kalshi Fed Markets" in result.output
    assert "KALSHI_API_KEY" in result.output


def test_info_exits_nonzero_for_unknown():
    with patch("prism.registry_client.RegistryClient.fetch", return_value={
        "version": "1.0", "updated_at": "2026-01-01T00:00:00Z", "connectors": []
    }):
        result = runner.invoke(app, ["info", "nonexistent"])
    assert result.exit_code != 0


# --- version ---

def test_version_prints_version_string():
    with patch("prism.registry_client.RegistryClient.fetch", return_value=SAMPLE_REGISTRY):
        result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "prism-signal" in result.output
    assert "0.1.0" in result.output
