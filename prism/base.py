from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import yaml


@dataclass
class PricePoint:
    timestamp: datetime
    price: float
    volume: int = 0
    slug: str = ""
    source: str = ""

    def __post_init__(self):
        if not (0.0 <= self.price <= 1.0):
            raise ValueError(f"price must be in [0.0, 1.0], got {self.price}")


@dataclass
class PrismMetadata:
    name: str
    slug: str
    version: str
    author: str
    source_type: str
    transport: str
    description: str
    auth_required: bool
    auth_fields: list[str] = field(default_factory=list)
    contract_slugs: list[str] = field(default_factory=list)
    homepage: str | None = None
    tags: list[str] = field(default_factory=list)


class PrismConnector(ABC):
    metadata: PrismMetadata

    @abstractmethod
    async def start(self) -> None:
        """Start the connector — open connections, begin streaming."""

    @abstractmethod
    async def stop(self) -> None:
        """Gracefully stop the connector and release all resources."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the connector is healthy and data is flowing."""


class PrismRegistry:
    def __init__(self):
        self._connectors: dict[str, type[PrismConnector]] = {}

    def register(self, cls: type[PrismConnector]) -> type[PrismConnector]:
        self._connectors[cls.metadata.slug] = cls
        return cls

    def get(self, slug: str) -> type[PrismConnector] | None:
        return self._connectors.get(slug)

    def all(self) -> list[type[PrismConnector]]:
        return list(self._connectors.values())

    def load_directory(self, path: Path) -> None:
        """Load all .prism packages from a directory, warn and skip bad ones."""
        import importlib.util
        import sys
        from rich.console import Console
        console = Console()

        path = Path(path)
        for pkg in path.glob("*.prism"):
            init_file = pkg / "__init__.py"
            manifest_file = pkg / "connector.prism"
            if not init_file.exists() or not manifest_file.exists():
                console.print(f"[yellow]WARN[/yellow] Skipping {pkg.name}: missing __init__.py or connector.prism")
                continue
            try:
                mod_key = f"_prism_pkg_{pkg.stem}"
                spec = importlib.util.spec_from_file_location(mod_key, init_file)
                mod = importlib.util.module_from_spec(spec)
                sys.modules[mod_key] = mod
                spec.loader.exec_module(mod)
                for attr in dir(mod):
                    obj = getattr(mod, attr)
                    if (
                        isinstance(obj, type)
                        and issubclass(obj, PrismConnector)
                        and obj is not PrismConnector
                        and hasattr(obj, "metadata")
                    ):
                        self.register(obj)
                        break
            except Exception as e:
                console.print(f"[yellow]WARN[/yellow] Skipping {pkg.name}: {e}")

    def summary(self) -> list[dict]:
        result = []
        for cls in self._connectors.values():
            m = cls.metadata
            result.append({
                "name": m.name,
                "slug": m.slug,
                "version": m.version,
                "transport": m.transport,
                "auth_required": m.auth_required,
                "status": "unknown",
            })
        return result


REQUIRED_MANIFEST_FIELDS = {
    "name": str,
    "slug": str,
    "version": str,
    "author": str,
    "source_type": str,
    "transport": str,
    "description": str,
    "auth_required": bool,
    "contract_slugs": list,
    "prism_format_version": str,
}


def validate_manifest(path: Path) -> dict:
    """Parse and validate connector.prism manifest. Raises ValueError on failure."""
    path = Path(path)
    if not path.exists():
        raise ValueError(f"Manifest not found: {path}")
    with open(path) as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("Manifest must be a YAML mapping")
    for field_name, expected_type in REQUIRED_MANIFEST_FIELDS.items():
        if field_name not in data:
            raise ValueError(f"Missing required field: {field_name}")
        if not isinstance(data[field_name], expected_type):
            raise ValueError(
                f"Field '{field_name}' must be {expected_type.__name__}, "
                f"got {type(data[field_name]).__name__}"
            )
    if data.get("prism_format_version") != "1.0":
        raise ValueError(
            f"prism_format_version must be '1.0', got {data.get('prism_format_version')!r}"
        )
    return data
