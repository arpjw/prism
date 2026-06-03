from __future__ import annotations
import json
import time
from pathlib import Path

import httpx
from rich.console import Console

REGISTRY_URL = "https://raw.githubusercontent.com/arpjw/prism/main/registry/registry.json"
CACHE_DIR = Path.home() / ".prism"
CACHE_FILE = CACHE_DIR / "registry_cache.json"
CACHE_TTL = 3600

console = Console()


class RegistryClient:
    def fetch(self) -> dict:
        """Fetch registry.json from GitHub. Falls back to local cache on network failure."""
        try:
            resp = httpx.get(REGISTRY_URL, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            self._write_cache(data)
            return data
        except Exception as e:
            cached = self._read_cache()
            if cached:
                console.print(f"[yellow]WARN[/yellow] Network error ({e}); using cached registry.")
                return cached
            raise RuntimeError(f"Cannot fetch registry and no cache available: {e}") from e

    def find(self, slug: str) -> dict | None:
        registry = self.fetch()
        for connector in registry.get("connectors", []):
            if connector.get("slug") == slug:
                return connector
        return None

    def search(self, tags: list[str] = [], source_type: str | None = None) -> list[dict]:
        registry = self.fetch()
        results = registry.get("connectors", [])
        if tags:
            results = [c for c in results if any(t in c.get("tags", []) for t in tags)]
        if source_type:
            results = [c for c in results if c.get("source_type") == source_type]
        return results

    def get_download_url(self, slug: str, version: str = "latest") -> str:
        connector = self.find(slug)
        if not connector:
            raise ValueError(f"Connector '{slug}' not found in registry")
        return connector.get("source_url", "")

    def _write_cache(self, data: dict) -> None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache = {"timestamp": time.time(), "data": data}
        CACHE_FILE.write_text(json.dumps(cache))

    def _read_cache(self) -> dict | None:
        if not CACHE_FILE.exists():
            return None
        try:
            cache = json.loads(CACHE_FILE.read_text())
            age = time.time() - cache.get("timestamp", 0)
            if age > CACHE_TTL:
                console.print("[yellow]WARN[/yellow] Registry cache is stale (>1h old).")
            return cache.get("data")
        except Exception:
            return None
