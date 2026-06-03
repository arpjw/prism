from __future__ import annotations
from pathlib import Path


MANIFEST_TEMPLATE = """\
prism_format_version: "1.0"
name: "{name}"
slug: "{slug}"
version: "1.0.0"
author: "{author}"
source_type: "{source_type}"
transport: "{transport}"
description: "TODO: describe what this connector streams."
auth_required: false
auth_fields: []
contract_slugs:
  - TODO_SLUG
tags: []
homepage: null
"""

INIT_TEMPLATE = '''\
"""
{name} PrismConnector
"""
from __future__ import annotations
import asyncio
from prism.base import PrismConnector, PrismMetadata, PricePoint


class {class_name}(PrismConnector):
    """Connector for {name}."""

    metadata = PrismMetadata(
        name="{name}",
        slug="{slug}",
        version="1.0.0",
        author="{author}",
        source_type="{source_type}",
        transport="{transport}",
        description="TODO: describe what this connector streams.",
        auth_required=False,
        auth_fields=[],
        contract_slugs=["TODO_SLUG"],
        tags=[],
    )

    async def start(self) -> None:
        """Open connections and begin streaming price data.

        1. Authenticate with the upstream source
        2. Open a WebSocket / start polling / begin push subscription
        3. On each new price, emit a PricePoint via your callback/queue
        """
        raise NotImplementedError

    async def stop(self) -> None:
        """Gracefully stop the connector and release all resources."""
        raise NotImplementedError

    async def health_check(self) -> bool:
        """Return True if the connector is healthy and data is flowing."""
        raise NotImplementedError
'''

SCHEMA_TEMPLATE = """\
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PricePoint",
  "type": "object",
  "required": ["timestamp", "price", "slug", "source"],
  "properties": {
    "timestamp": {"type": "string", "format": "date-time"},
    "price": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    "volume": {"type": "integer", "minimum": 0},
    "slug": {"type": "string"},
    "source": {"type": "string"}
  }
}
"""

README_TEMPLATE = """\
# {name}

Prism connector for {name}.

## Overview

TODO: describe what this connector streams, the upstream data source, and how prices are
normalized to [0.0, 1.0].

## Auth

| Env Var | Required | Description |
|---------|----------|-------------|
| TODO_KEY | Yes | TODO: description |

## Config

TODO: any additional configuration options.

## Emitted Signals

| Contract Slug | Description |
|---------------|-------------|
| TODO_SLUG | TODO: description |

## Example Output

```
PricePoint(timestamp=2026-01-01T00:00:00+00:00, price=0.72, volume=150, slug="TODO_SLUG", source="{slug}")
```

## Installation

```bash
pip install prism-signal
prism install {slug}
```
"""

TEST_TEMPLATE = '''\
"""Tests for {name} connector."""
from pathlib import Path

CONNECTOR_DIR = Path(__file__).parent.parent


def test_manifest_exists():
    assert (CONNECTOR_DIR / "connector.prism").exists()


def test_init_exists():
    assert (CONNECTOR_DIR / "__init__.py").exists()


def test_readme_exists():
    assert (CONNECTOR_DIR / "README.md").exists()


def test_schema_exists():
    assert (CONNECTOR_DIR / "schema.json").exists()


def test_spec_loads():
    import importlib.util
    spec = importlib.util.spec_from_file_location("{slug}", CONNECTOR_DIR / "__init__.py")
    assert spec is not None
'''


def _to_class_name(slug: str) -> str:
    return "".join(part.capitalize() for part in slug.split("_")) + "Connector"


def _get_git_author() -> str:
    import subprocess
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True, text=True, timeout=5,
        )
        name = result.stdout.strip()
        return name if name else "unknown"
    except Exception:
        return "unknown"


def scaffold_connector(
    name: str,
    slug: str,
    source_type: str,
    transport: str,
    output_dir: Path,
    author: str | None = None,
) -> Path:
    if author is None:
        author = _get_git_author()

    pkg_dir = output_dir / f"{slug}.prism"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / "tests").mkdir(exist_ok=True)

    class_name = _to_class_name(slug)

    (pkg_dir / "connector.prism").write_text(
        MANIFEST_TEMPLATE.format(
            name=name, slug=slug, author=author,
            source_type=source_type, transport=transport,
        )
    )
    (pkg_dir / "__init__.py").write_text(
        INIT_TEMPLATE.format(
            name=name, slug=slug, author=author,
            source_type=source_type, transport=transport,
            class_name=class_name,
        )
    )
    (pkg_dir / "schema.json").write_text(SCHEMA_TEMPLATE)
    (pkg_dir / "README.md").write_text(README_TEMPLATE.format(name=name, slug=slug))
    (pkg_dir / "tests" / f"test_{slug}.py").write_text(
        TEST_TEMPLATE.format(name=name, slug=slug)
    )

    return pkg_dir
