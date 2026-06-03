from __future__ import annotations
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(help="Prism — connector framework for velocity signal engines.")
console = Console()


@app.command()
def scaffold(
    name: str = typer.Option(..., help="Human-readable connector name"),
    slug: str = typer.Option(..., help="Machine-readable slug (snake_case)"),
    type_: str = typer.Option(..., "--type", help="prediction_market|alternative_data|news|custom"),
    transport: str = typer.Option(..., help="websocket|rest|push"),
    output_dir: Path = typer.Option(Path("./connectors"), "--output-dir"),
    author: Optional[str] = typer.Option(None, help="Author name or GitHub username"),
):
    """Scaffold a new .prism connector package."""
    from prism.scaffold import scaffold_connector
    pkg_dir = scaffold_connector(
        name=name,
        slug=slug,
        source_type=type_,
        transport=transport,
        output_dir=output_dir,
        author=author,
    )
    console.print(Panel(
        f"\n[bold]📁  {pkg_dir}/[/bold]\n\n"
        "Next steps:\n"
        f"  1. Fill in connector.prism — auth_fields, contract_slugs\n"
        f"  2. Implement start(), stop(), health_check()\n"
        f"  3. Run: [cyan]prism validate {pkg_dir}[/cyan]\n"
        f"  4. Drop into your engine's connectors/ and restart\n",
        title="Prism connector scaffolded",
        border_style="green",
    ))


@app.command()
def validate(
    path: Path = typer.Argument(..., help="Path to a .prism directory package"),
):
    """Validate a .prism connector package."""
    from prism.validator import validate_connector, print_validation_table
    results, exit_code = validate_connector(path)
    print_validation_table(results, path)
    raise typer.Exit(exit_code)


@app.command("list")
def list_connectors(
    installed: bool = typer.Option(False, "--installed", help="Show locally installed connectors"),
    registry: bool = typer.Option(False, "--registry", help="Show connectors from the registry"),
    tags: Optional[list[str]] = typer.Option(None, "--tags", help="Filter by tag"),
    type_: Optional[str] = typer.Option(None, "--type", help="Filter by source_type"),
):
    """List available connectors."""
    import yaml
    from prism.registry_client import RegistryClient

    connectors: list[dict] = []

    if installed or not registry:
        cwd_connectors = Path("connectors")
        if cwd_connectors.exists():
            for pkg in cwd_connectors.glob("*.prism"):
                manifest_path = pkg / "connector.prism"
                if manifest_path.exists():
                    try:
                        data = yaml.safe_load(manifest_path.read_text())
                        data["_installed"] = True
                        connectors.append(data)
                    except Exception:
                        pass

    if registry:
        try:
            client = RegistryClient()
            reg = client.fetch()
            registry_connectors = reg.get("connectors", [])
            installed_slugs = {c.get("slug") for c in connectors}
            for rc in registry_connectors:
                rc["_installed"] = rc.get("slug") in installed_slugs
                connectors.append(rc)
        except Exception as e:
            console.print(f"[yellow]WARN[/yellow] Could not fetch registry: {e}")

    if installed:
        connectors = [c for c in connectors if c.get("_installed")]

    if tags:
        connectors = [c for c in connectors if any(t in c.get("tags", []) for t in tags)]
    if type_:
        connectors = [c for c in connectors if c.get("source_type") == type_]

    # Deduplicate by slug, keeping last
    seen: dict[str, dict] = {}
    for c in connectors:
        seen[c.get("slug", "")] = c
    connectors = list(seen.values())

    table = Table(show_header=True, header_style="bold")
    table.add_column("Name")
    table.add_column("Slug", style="dim")
    table.add_column("Version")
    table.add_column("Transport")
    table.add_column("Tags")
    table.add_column("Installed", justify="center")

    for c in connectors:
        table.add_row(
            c.get("name", ""),
            c.get("slug", ""),
            c.get("version", ""),
            c.get("transport", ""),
            ", ".join(c.get("tags", [])),
            "✓" if c.get("_installed") else "–",
        )

    console.print(table)


@app.command()
def install(
    slug: str = typer.Argument(..., help="Connector slug from the registry"),
    version: str = typer.Option("latest", "--version"),
    output_dir: Path = typer.Option(Path("./connectors"), "--output-dir"),
    force: bool = typer.Option(False, "--force", help="Overwrite if already installed"),
):
    """Install a connector from the registry."""
    from prism.installer import install_connector
    try:
        install_connector(slug=slug, output_dir=output_dir, version=version, force=force)
    except FileExistsError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def info(
    slug: str = typer.Argument(..., help="Connector slug"),
):
    """Show full details for a connector from the registry."""
    from prism.registry_client import RegistryClient
    client = RegistryClient()
    connector = client.find(slug)
    if not connector:
        console.print(f"[red]Error:[/red] Connector '{slug}' not found in registry")
        raise typer.Exit(1)

    console.print(
        f"\n[bold]{connector.get('name')}[/bold]  "
        f"[dim]{connector.get('slug')}[/dim]  "
        f"v{connector.get('version')}"
    )
    console.print(f"[dim]{connector.get('description')}[/dim]\n")
    console.print(f"Author:      {connector.get('author')}")
    console.print(f"Source type: {connector.get('source_type')}")
    console.print(f"Transport:   {connector.get('transport')}")
    console.print(f"Auth:        {'Required' if connector.get('auth_required') else 'Public'}")
    if connector.get("auth_fields"):
        console.print(f"Auth fields: {', '.join(connector['auth_fields'])}")
    console.print(f"Tags:        {', '.join(connector.get('tags', []))}")
    console.print(f"Contracts:   {', '.join(connector.get('contract_slugs', []))}")
    if connector.get("homepage"):
        console.print(f"Homepage:    {connector['homepage']}")
    console.print(f"Verified:    {'Yes' if connector.get('verified') else 'No'}")
    console.print(f"\nInstall:\n  [cyan]prism install {slug}[/cyan]")


@app.command()
def version():
    """Print prism-signal version and registry info."""
    from prism import __version__
    from prism.registry_client import RegistryClient, REGISTRY_URL
    console.print(f"prism-signal v{__version__}")
    console.print(f"Registry: {REGISTRY_URL}")
    try:
        client = RegistryClient()
        reg = client.fetch()
        console.print(f"Registry version: {reg.get('version', 'unknown')}")
        console.print(f"Registry updated: {reg.get('updated_at', 'unknown')}")
    except Exception as e:
        console.print(f"[yellow]WARN[/yellow] Could not fetch registry: {e}")


if __name__ == "__main__":
    app()
