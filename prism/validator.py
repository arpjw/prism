from __future__ import annotations
import importlib.util
import sys
from pathlib import Path
from typing import NamedTuple

from rich.console import Console
from rich.table import Table

from prism.base import validate_manifest, PrismConnector

console = Console()


class CheckResult(NamedTuple):
    name: str
    passed: bool
    is_warning: bool
    message: str


def validate_connector(path: Path) -> tuple[list[CheckResult], int]:
    """Validate a .prism package. Returns (results, exit_code)."""
    path = Path(path).resolve()
    results: list[CheckResult] = []

    # 1. connector.prism exists and is valid YAML
    manifest_path = path / "connector.prism"
    manifest = None
    try:
        manifest = validate_manifest(manifest_path)
        results.append(CheckResult("Manifest exists and valid YAML", True, False, ""))
    except Exception as e:
        results.append(CheckResult("Manifest exists and valid YAML", False, False, str(e)))

    # 2. Required fields present
    if manifest is not None:
        results.append(CheckResult("Required fields present", True, False, ""))
    else:
        results.append(CheckResult("Required fields present", False, False, "Manifest failed to load"))

    # 3. prism format version
    if manifest is not None:
        fv = manifest.get("prism_format_version")
        if fv == "1.0":
            results.append(CheckResult("Format version is '1.0'", True, False, ""))
        else:
            results.append(CheckResult("Format version is '1.0'", False, False, f"Got: {fv!r}"))

    # 4. __init__.py exists
    init_path = path / "__init__.py"
    if init_path.exists():
        results.append(CheckResult("__init__.py exists", True, False, ""))
    else:
        results.append(CheckResult("__init__.py exists", False, False, ""))

    # 5. PrismConnector subclass exists and is importable
    connector_class = None
    if init_path.exists():
        try:
            mod_key = f"_prism_validate_{path.stem}_{id(path)}"
            spec = importlib.util.spec_from_file_location(mod_key, init_path)
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
                    connector_class = obj
                    break
            if connector_class:
                results.append(CheckResult("PrismConnector subclass found", True, False, ""))
            else:
                results.append(CheckResult(
                    "PrismConnector subclass found", False, False,
                    "No PrismConnector subclass found in __init__.py"
                ))
        except Exception as e:
            results.append(CheckResult("PrismConnector subclass found", False, False, str(e)))
    else:
        results.append(CheckResult("PrismConnector subclass found", False, False, "__init__.py missing"))

    # 6. metadata.slug matches manifest slug
    if connector_class and manifest:
        class_slug = getattr(getattr(connector_class, "metadata", None), "slug", None)
        manifest_slug = manifest.get("slug")
        if class_slug == manifest_slug:
            results.append(CheckResult("metadata.slug matches manifest", True, False, ""))
        else:
            results.append(CheckResult(
                "metadata.slug matches manifest", False, False,
                f"class={class_slug!r}, manifest={manifest_slug!r}"
            ))

    # 7. metadata.version matches manifest version
    if connector_class and manifest:
        class_ver = getattr(getattr(connector_class, "metadata", None), "version", None)
        manifest_ver = manifest.get("version")
        if class_ver == manifest_ver:
            results.append(CheckResult("metadata.version matches manifest", True, False, ""))
        else:
            results.append(CheckResult(
                "metadata.version matches manifest", False, False,
                f"class={class_ver!r}, manifest={manifest_ver!r}"
            ))

    # 8. Auth fields documented in README
    if manifest:
        auth_fields = manifest.get("auth_fields", [])
        readme_path = path / "README.md"
        if auth_fields:
            if readme_path.exists():
                readme_text = readme_path.read_text()
                undocumented = [f for f in auth_fields if f not in readme_text]
                if undocumented:
                    results.append(CheckResult(
                        "Auth fields in README", True, True,
                        f"{', '.join(undocumented)} not found in README.md"
                    ))
                else:
                    results.append(CheckResult("Auth fields in README", True, False, ""))
            else:
                results.append(CheckResult("Auth fields in README", True, True, "README.md not found"))
        else:
            results.append(CheckResult("Auth fields in README", True, False, "No auth fields"))

    # 9. contract_slugs is non-empty list
    if manifest:
        cs = manifest.get("contract_slugs", [])
        if isinstance(cs, list) and len(cs) > 0:
            results.append(CheckResult("contract_slugs non-empty", True, False, ""))
        else:
            results.append(CheckResult(
                "contract_slugs non-empty", False, False,
                "contract_slugs must be a non-empty list"
            ))

    # 10. Tests present
    tests_dir = path / "tests"
    if tests_dir.exists():
        test_files = list(tests_dir.glob("test_*.py"))
        if test_files:
            results.append(CheckResult("Tests present", True, False, ""))
        else:
            results.append(CheckResult(
                "Tests present", True, True,
                "tests/ exists but no test_*.py files found"
            ))
    else:
        results.append(CheckResult("Tests present", True, True, "No tests/ directory found"))

    failures = [r for r in results if not r.passed and not r.is_warning]
    exit_code = 1 if failures else 0
    return results, exit_code


def print_validation_table(results: list[CheckResult], path: Path) -> tuple[int, int]:
    table = Table(show_header=True, header_style="bold", box=None)
    table.add_column("Check", min_width=35)
    table.add_column("Result", justify="center", min_width=8)
    table.add_column("Message")

    failures = 0
    warnings = 0

    for r in results:
        if not r.passed and not r.is_warning:
            result_str = "[red]FAIL[/red]"
            failures += 1
        elif r.is_warning and r.message:
            result_str = "[yellow]WARN[/yellow]"
            warnings += 1
        else:
            result_str = "[green]PASS[/green]"
        table.add_row(r.name, result_str, r.message)

    console.print(f"\n[bold]Validating:[/bold] {path}\n")
    console.print(table)

    if failures == 0 and warnings == 0:
        console.print("\n[green]Overall: PASS[/green]")
    elif failures == 0:
        console.print(f"\n[green]Overall: PASS[/green] ({warnings} warning{'s' if warnings != 1 else ''})")
    else:
        console.print(
            f"\n[red]Overall: FAIL[/red] "
            f"({failures} failure{'s' if failures != 1 else ''}, "
            f"{warnings} warning{'s' if warnings != 1 else ''})"
        )

    return failures, warnings
