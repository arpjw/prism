# PRISM

**Connector framework for velocity signal engines.**

[![PyPI](https://img.shields.io/pypi/v/prism-signal)](https://pypi.org/project/prism-signal/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://github.com/arpjw/prism/actions/workflows/validate_registry.yml/badge.svg)](https://github.com/arpjw/prism/actions)

---

## What is Prism?

**The problem.** Velocity signal engines need a standard way to ingest data from heterogeneous
sources — prediction markets, economic APIs, news feeds. Without a common interface, every engine
reimplements the same polling, authentication, normalization, and health-check logic.

**The solution.** `.prism` is a self-contained connector format. Any data source that produces a
time series can be a connector. The `PrismConnector` interface handles the contract; the developer
handles the source. Install with one command, validate with one command, drop into any compatible
engine.

**The ecosystem.** A GitHub-backed registry of community connectors, installable with `prism install`.
Browse available connectors at [prism.aryasomu.com](https://prism.aryasomu.com).

---

## Installation

```bash
pip install prism-signal
```

**prism-signal is live on PyPI:** https://pypi.org/project/prism-signal/

Requires Python 3.11+.

---

## Quickstart

```bash
pip install prism-signal  # live on PyPI

prism list --registry

prism install kalshi_fed

prism scaffold --name "My Source" --slug my_source --type prediction_market --transport rest

prism validate connectors/my_source.prism
```

---

## Built-in connectors

| Name | Slug | Source | Transport | Auth | Tags |
|------|------|--------|-----------|------|------|
| Kalshi Fed Markets | `kalshi_fed` | Kalshi | WebSocket | Required | fed, rates, macro |
| Polymarket Macro | `polymarket_macro` | Polymarket | WebSocket | None | fed, rates, macro |
| Metaculus Macro | `metaculus_macro` | Metaculus | REST | None | fed, macro, forecasting |
| Manifold Macro | `manifold_macro` | Manifold | REST | None | fed, macro |
| FRED Macro | `fred_macro` | FRED (St. Louis Fed) | REST | Required | fed, rates, economic-data |

---

## CLI reference

| Command | Description |
|---------|-------------|
| `prism scaffold --name X --slug x --type T --transport T` | Create a new .prism connector package |
| `prism validate <path>` | Validate a .prism package (exit 0 = pass/warn, exit 1 = fail) |
| `prism list [--installed] [--registry] [--tags T] [--type T]` | List connectors |
| `prism install <slug> [--force] [--output-dir D]` | Install from registry |
| `prism info <slug>` | Show connector details from registry |
| `prism version` | Print version and registry info |

---

## The .prism format

A `.prism` package is a directory named `{slug}.prism/` containing:

```
my_source.prism/
  connector.prism    # YAML manifest
  __init__.py        # PrismConnector subclass
  schema.json        # PricePoint JSON Schema
  README.md          # Documentation
  tests/             # Test suite
```

**connector.prism schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| prism_format_version | string | Yes | Must be `"1.0"` |
| name | string | Yes | Human-readable display name |
| slug | string | Yes | snake_case machine identifier |
| version | string | Yes | Semver version string |
| author | string | Yes | Author name or GitHub username |
| source_type | string | Yes | `prediction_market`, `alternative_data`, `news`, `custom` |
| transport | string | Yes | `websocket`, `rest`, `push` |
| description | string | Yes | One-sentence description |
| auth_required | bool | Yes | Whether env vars are needed |
| auth_fields | list[str] | No | Names of required env vars |
| contract_slugs | list[str] | Yes | Market/contract identifiers |
| tags | list[str] | No | Searchable tags |
| homepage | string | No | URL to docs or source |

---

## PrismConnector interface

Every connector must implement three async methods:

```python
class MyConnector(PrismConnector):
    async def start(self) -> None:
        """Open connections and begin streaming price data."""

    async def stop(self) -> None:
        """Gracefully close connections and release resources."""

    async def health_check(self) -> bool:
        """Return True if the connector is healthy and data is flowing."""
```

---

## The PricePoint contract

Every emission must be a valid `PricePoint`:

| Field | Type | Description |
|-------|------|-------------|
| timestamp | datetime | UTC-aware timestamp of the observation |
| price | float | Normalized probability in **[0.0, 1.0]** — required |
| volume | int | Raw volume (0 if unavailable) |
| slug | str | Contract/market slug this price belongs to |
| source | str | Connector slug that emitted this point |

**Normalization is the connector's responsibility.** If your source emits cents, divide by 100.
If it emits a rate percentage, normalize against a known range.

```python
PricePoint(
    timestamp=datetime.now(timezone.utc),
    price=0.72,                  # must be in [0.0, 1.0]
    volume=1500,
    slug="KXFED",
    source="kalshi_fed",
)
```

---

## Contributing a connector

Build a connector with `prism scaffold`, implement the three abstract methods, validate with
`prism validate`, and open a PR to `arpjw/prism`. Full guide: [CONTRIBUTING_CONNECTORS.md](CONTRIBUTING_CONNECTORS.md).

---

## License

MIT — see [LICENSE](LICENSE).
