# Contributing Connectors to Prism

This guide covers everything you need to build, validate, and submit a connector to the Prism registry.

---

## 1. What is a connector?

A Prism connector is a self-contained `.prism` directory package that streams or polls a data source
and emits `PricePoint` objects — normalized probability values in [0.0, 1.0]. Any source that produces
a time series (prediction markets, economic data, news sentiment) can be a connector.

---

## 2. Quickstart

```bash
pip install prism-signal

prism scaffold \
  --name "My Data Source" \
  --slug my_source \
  --type prediction_market \
  --transport rest

prism validate connectors/my_source.prism
```

This creates `connectors/my_source.prism/` with a manifest, skeleton implementation, schema, README,
and test scaffold.

---

## 3. Directory structure

```
my_source.prism/
  connector.prism    # YAML manifest (required)
  __init__.py        # PrismConnector subclass (required)
  schema.json        # PricePoint JSON Schema
  README.md          # Documentation
  tests/
    test_my_source.py
```

---

## 4. The connector.prism manifest

```yaml
prism_format_version: "1.0"
name: "My Data Source"
slug: "my_source"
version: "1.0.0"
author: "your_github_username"
source_type: "prediction_market"  # prediction_market | alternative_data | news | custom
transport: "rest"                  # websocket | rest | push
description: "Streams XYZ prices from ABC API."
auth_required: true
auth_fields:
  - MY_API_KEY
contract_slugs:
  - MY_CONTRACT_SLUG
tags:
  - macro
  - rates
homepage: "https://github.com/you/your-repo"
```

---

## 5. Implementing PrismConnector

Your `__init__.py` must define a class that inherits from `PrismConnector` and implements three methods:

```python
from prism.base import PrismConnector, PrismMetadata, PricePoint
from datetime import datetime, timezone

class MySourceConnector(PrismConnector):
    metadata = PrismMetadata(
        name="My Data Source",
        slug="my_source",
        version="1.0.0",
        author="your_github_username",
        source_type="prediction_market",
        transport="rest",
        description="Streams XYZ prices from ABC API.",
        auth_required=True,
        auth_fields=["MY_API_KEY"],
        contract_slugs=["MY_CONTRACT_SLUG"],
        tags=["macro"],
    )

    async def start(self) -> None:
        """Open connections and begin emitting PricePoints."""
        ...

    async def stop(self) -> None:
        """Gracefully close connections and release resources."""
        ...

    async def health_check(self) -> bool:
        """Return True if the connector is healthy and streaming."""
        ...
```

---

## 6. The PricePoint contract

Every emission must be a valid `PricePoint`:

```python
PricePoint(
    timestamp=datetime.now(timezone.utc),  # must be UTC-aware
    price=0.72,                             # MUST be in [0.0, 1.0]
    volume=1500,                            # optional: raw volume
    slug="MY_CONTRACT_SLUG",               # which contract this is for
    source="my_source",                    # your connector's slug
)
```

**Normalization is your responsibility.** If your source emits prices in cents, divide by 100.
If it emits a raw rate (e.g., 5.25%), normalize against a known range.

---

## 7. Writing tests

Every connector needs at least 5 tests in `tests/test_{slug}.py`:

```python
def test_manifest_exists(): ...
def test_metadata_slug_matches(): ...
def test_health_check_false_when_not_running(): ...
def test_price_normalization(): ...
def test_no_auth_when_not_required(): ...
```

Run with: `pytest connectors/my_source.prism/tests/`

---

## 8. Validation

Before submitting, your connector must pass `prism validate` with zero failures:

```bash
prism validate connectors/my_source.prism
```

Warnings are acceptable (e.g., missing tests dir, undocumented auth fields), but failures block submission.

---

## 9. Submitting to the registry

1. Fork `arpjw/prism` on GitHub
2. Copy your `.prism` package to `connectors/your_slug.prism/`
3. Add an entry to `registry/registry.json` (see Section 10 below)
4. Open a PR — CI will automatically run `prism validate` on your connector
5. A maintainer will review and merge

CI checks:
- `registry/registry.json` validates against `registry/schema.json`
- `prism validate` passes with zero failures on your connector
- No imports from private or non-prism packages

---

## 10. Registry entry

When you submit a connector, add an entry to `registry/registry.json`:

```json
{
  "name": "My Data Source",
  "slug": "my_source",
  "version": "1.0.0",
  "author": "your_github_username",
  "source_type": "prediction_market",
  "transport": "rest",
  "description": "One sentence describing what this streams.",
  "auth_required": true,
  "auth_fields": ["MY_API_KEY"],
  "contract_slugs": ["MY_CONTRACT_SLUG"],
  "tags": ["macro", "rates"],
  "homepage": "https://github.com/you/your-repo",
  "source_url": "https://github.com/arpjw/prism/archive/refs/heads/main.tar.gz",
  "source_path": "connectors/my_source.prism",
  "downloads": 0,
  "verified": false
}
```

**Field reference:**

| Field | Required | Description |
|-------|----------|-------------|
| name | Yes | Human-readable display name |
| slug | Yes | snake_case identifier, must match your package directory |
| version | Yes | semver (e.g., 1.0.0) |
| author | Yes | GitHub username of the connector author |
| source_type | Yes | One of: prediction_market, alternative_data, news, custom |
| transport | Yes | One of: websocket, rest, push |
| description | Yes | One sentence, what this connector streams |
| auth_required | Yes | true if the connector requires env vars to operate |
| auth_fields | Yes | List of required env var names |
| contract_slugs | Yes | List of contract/market identifiers this connector tracks |
| tags | Yes | Searchable tags (e.g., fed, rates, macro, recession) |
| homepage | No | URL to your repo, docs, or source |
| source_url | Yes | GitHub archive URL where the package can be downloaded |
| source_path | Yes | Path within the archive to the .prism directory |
| downloads | Yes | Set to 0 on submission (managed by maintainers) |
| verified | Yes | Set to false on submission. The maintainer sets this to true after review and live testing |

**What does `"verified": true` mean?**
A maintainer has reviewed the code, confirmed it imports only from `prism.*`, run it against a live data source, and verified the normalization is correct. Community-submitted connectors default to `false` — use them at your own risk until they are verified.
