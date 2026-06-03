from __future__ import annotations
import shutil
import tarfile
import tempfile
from pathlib import Path

import httpx
from rich.console import Console

from prism.registry_client import RegistryClient
from prism.validator import validate_connector, print_validation_table

console = Console()


def install_connector(
    slug: str,
    output_dir: Path,
    version: str = "latest",
    force: bool = False,
) -> Path:
    client = RegistryClient()
    connector = client.find(slug)
    if not connector:
        raise ValueError(f"Connector '{slug}' not found in registry")

    dest = output_dir / f"{slug}.prism"
    if dest.exists() and not force:
        raise FileExistsError(f"{dest} already exists. Use --force to overwrite.")

    source_url = connector.get("source_url", "")
    source_path = connector.get("source_path", f"connectors/{slug}.prism")

    console.print(f"Downloading [bold]{slug}[/bold] from registry...")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        archive_path = tmp_path / "connector.tar.gz"

        try:
            with httpx.stream("GET", source_url, timeout=30.0, follow_redirects=True) as resp:
                resp.raise_for_status()
                with open(archive_path, "wb") as f:
                    for chunk in resp.iter_bytes():
                        f.write(chunk)
        except Exception as e:
            raise RuntimeError(f"Failed to download connector: {e}") from e

        try:
            with tarfile.open(archive_path) as tar:
                tar.extractall(tmp_path)
        except Exception as e:
            raise RuntimeError(f"Failed to extract connector archive: {e}") from e

        extracted_pkg = None
        for item in tmp_path.rglob(f"{slug}.prism"):
            if item.is_dir():
                extracted_pkg = item
                break

        if not extracted_pkg:
            candidates = list(tmp_path.glob(f"*/{source_path}")) + list(tmp_path.glob(source_path))
            extracted_pkg = next((c for c in candidates if c.is_dir()), None)

        if not extracted_pkg:
            raise RuntimeError(f"Could not find {slug}.prism in downloaded archive")

        results, exit_code = validate_connector(extracted_pkg)
        print_validation_table(results, extracted_pkg)

        if exit_code != 0:
            raise RuntimeError("Connector validation failed. Aborting install.")

        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(extracted_pkg, dest)

    console.print(f"\n[green]Installed[/green] [bold]{slug}[/bold] → {dest}")
    console.print("\nNext steps:")
    console.print(f"  1. Set required env vars (see {dest}/README.md)")
    console.print(f"  2. Drop {dest}/ into your engine's connectors/ directory")
    console.print(f"  3. Restart your engine")

    return dest
