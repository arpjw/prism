# Prism — Standalone Project Build Plan

Prism is a standalone connector framework and registry for velocity signal engines. It extracts the `.prism` format from the Robinhood project into an independent, publishable ecosystem: a CLI tool, a PyPI package, a GitHub-backed connector registry, and a hosted marketplace UI at prism.aryasomu.com.

PyPI package: `prism-signal`
CLI command: `prism`
Registry: GitHub-backed JSON index
UI: Next.js, hosted on Vercel at prism.aryasomu.com

---

## Repo Structure

```
prism/
  prism/                        # core Python package (prism-signal on PyPI)
    __init__.py
    base.py                     # PrismConnector, PrismMetadata, PrismRegistry, PricePoint
    scaffold.py                 # scaffold command implementation
    validator.py                # validate command implementation
    installer.py                # install command implementation
    cli.py                      # top-level CLI entrypoint (typer)
    registry_client.py          # reads/queries registry.json from GitHub
  connectors/                   # built-in connectors shipped with the package
    kalshi_fed.prism/
    polymarket_macro.prism/
    metaculus_macro.prism/
    manifold_macro.prism/
    fred_macro.prism/
  registry/
    registry.json               # the connector registry index
    schema.json                 # JSON schema for registry.json
  ui/                           # Next.js marketplace UI
    app/
    components/
  tests/
  CONTRIBUTING_CONNECTORS.md
  pyproject.toml
  README.md
```

---

## Prompt 1 — Core Package and CLI

```
Initialize the prism repo as a standalone Python project. Build the core prism-signal package with a full CLI.

---

PART A — Package Setup

pyproject.toml (PEP 621, no setup.py):
  [project]
  name = "prism-signal"
  version = "0.1.0"
  description = "Connector framework for velocity signal engines"
  requires-python = ">=3.11"
  dependencies = [
    "typer>=0.12.0",
    "pyyaml>=6.0",
    "httpx>=0.27.0",
    "rich>=13.0.0",
    "websockets>=12.0",
    "python-dotenv>=1.0.0",
  ]

  [project.scripts]
  prism = "prism.cli:app"

  [build-system]
  requires = ["hatchling"]
  build-backend = "hatchling.build"

---

PART B — Base Types (prism/base.py)

Copy and expand from the robinhood project's connectors/base.py. Additions and changes:

PricePoint dataclass (moved here from signals/velocity.py in robinhood):
  timestamp: datetime           # must be UTC-aware
  price: float                  # must be 0.0-1.0, enforced by __post_init__
  volume: int = 0
  slug: str = ""                # contract slug this price point belongs to
  source: str = ""              # connector slug that emitted this point

  __post_init__ validates price is in [0.0, 1.0] and raises ValueError if not.

PrismMetadata dataclass: identical to robinhood version plus two new fields:
  homepage: str | None = None   # URL to connector docs or source
  tags: list[str] = field(default_factory=list)   # e.g. ["fed", "rates", "macro"]

PrismConnector ABC: identical to robinhood version. No changes.

PrismRegistry: identical plus one new method:
  def summary(self) -> list[dict]:
    # Returns list of {name, slug, version, transport, auth_required, status} for all connectors.
    # Status comes from health_check().

validate_manifest(path): identical to robinhood version.

---

PART C — CLI (prism/cli.py)

Use typer for the CLI. The top-level app is `prism`. Subcommands:

prism scaffold
  Options:
    --name TEXT         Human-readable connector name [required]
    --slug TEXT         Machine-readable slug, snake_case [required]
    --type TEXT         source_type: prediction_market|alternative_data|news|custom [required]
    --transport TEXT    websocket|rest|push [required]
    --output-dir PATH   Where to create the .prism package (default: ./connectors/)
    --author TEXT       Author name or GitHub username (default: reads from git config)

  Behavior:
    Creates {output-dir}/{slug}.prism/ with:
    - connector.prism: manifest pre-filled with provided values, placeholder fields for auth_fields, contract_slugs, description
    - __init__.py: skeleton PrismConnector subclass with all abstract methods stubbed and detailed docstrings
    - schema.json: PricePoint schema
    - README.md: template with Overview, Auth, Config, Emitted Signals sections
    - tests/test_{slug}.py: skeleton test file with 3 placeholder tests

    After creation, prints a styled rich panel:
    ╭─ Prism connector scaffolded ─────────────────────────────╮
    │                                                           │
    │  📁  connectors/my_source.prism/                         │
    │                                                           │
    │  Next steps:                                              │
    │  1. Fill in connector.prism — auth_fields, contract_slugs │
    │  2. Implement start(), stop(), health_check()             │
    │  3. Run: prism validate connectors/my_source.prism        │
    │  4. Drop into your engine's connectors/ and restart       │
    │                                                           │
    ╰───────────────────────────────────────────────────────────╯

prism validate <path>
  Positional: path to a .prism directory package.
  
  Checks (print pass/fail/warn for each):
  1. connector.prism exists and is valid YAML
  2. All required manifest fields present and correctly typed
  3. prism format version is "1.0"
  4. __init__.py exists and is importable
  5. A PrismConnector subclass exists in __init__.py
  6. Class metadata.slug matches manifest slug
  7. Class metadata.version matches manifest version
  8. All auth_fields are documented in README.md
  9. contract_slugs field is a non-empty list
  10. If tests/ exists, at least one test file is present

  Output format (rich table):
  ┌─────────────────────────────────┬────────┬──────────────────────────────┐
  │ Check                           │ Result │ Message                      │
  ├─────────────────────────────────┼────────┼──────────────────────────────┤
  │ Manifest exists                 │  PASS  │                              │
  │ Required fields                 │  PASS  │                              │
  │ PrismConnector subclass         │  PASS  │                              │
  │ Auth fields documented          │  WARN  │ MYKEY not found in README.md │
  │ Tests present                   │  WARN  │ No tests/ directory found    │
  └─────────────────────────────────┴────────┴──────────────────────────────┘
  
  Overall: PASS (2 warnings)

  Exit 0 if no failures (warnings are OK). Exit 1 if any check fails.

prism list
  Options:
    --installed         Show only locally installed connectors (reads connectors/ in cwd)
    --registry          Show connectors available in the registry (fetches registry.json)
    --tags TEXT         Filter by tag, repeatable: --tags fed --tags rates
    --type TEXT         Filter by source_type

  Output: rich table with columns: name, slug, version, transport, tags, installed (✓/–)

  If --registry and network is unavailable, fall back to cached registry (see installer.py) with a WARN.

prism install <slug>
  Positional: connector slug from the registry.
  Options:
    --version TEXT      Install specific version (default: latest)
    --output-dir PATH   Where to install (default: ./connectors/)
    --force             Overwrite if already installed

  Behavior (see registry_client.py for implementation):
  1. Fetch registry.json
  2. Find connector by slug
  3. Download .prism package from the GitHub source_url in the registry entry
  4. Run validate on it — if validation fails, abort with error
  5. Copy to output-dir
  6. Print success with next steps

  On failure: print clear error, never leave partial directory behind (clean up on error).

prism info <slug>
  Shows full details for a connector from the registry: manifest fields, description, auth requirements, tags, version history if available.

prism version
  Prints prism-signal version and registry.json commit SHA.

---

PART D — Registry Client (prism/registry_client.py)

REGISTRY_URL = "https://raw.githubusercontent.com/arpjw/prism/main/registry/registry.json"

RegistryClient class:
  fetch() -> dict: GET registry.json, parse, return. Cache result in ~/.prism/registry_cache.json with a 1-hour TTL. If network fails, use cache with a WARN.
  find(slug: str) -> dict | None: find connector entry by slug.
  search(tags: list[str] = [], source_type: str = None) -> list[dict]: filter registry.
  get_download_url(slug: str, version: str = "latest") -> str: returns the GitHub download URL for the connector package.

Cache location: ~/.prism/registry_cache.json. Create ~/.prism/ on first use.

---

PART E — Tests

tests/test_cli.py: at least 15 tests using typer's CliRunner covering:
- prism scaffold creates correct directory structure
- prism scaffold with --author sets author in manifest
- prism validate passes on a valid .prism package
- prism validate fails (exit 1) on missing manifest
- prism validate fails on missing PrismConnector subclass
- prism validate warns (exit 0) on missing tests
- prism validate warns on undocumented auth field
- prism list --installed reads connectors/ in cwd
- prism list --registry fetches and displays registry
- prism list --tags filters correctly
- prism install downloads and validates a connector (mock HTTP)
- prism install aborts on validation failure
- prism install --force overwrites existing
- prism info shows connector details
- prism version prints version string

tests/test_base.py: at least 10 tests covering:
- PricePoint rejects price > 1.0
- PricePoint rejects price < 0.0
- PricePoint accepts boundary values 0.0 and 1.0
- PrismMetadata field validation
- PrismRegistry.load_directory with valid package
- PrismRegistry.load_directory with malformed package (warn and skip)
- PrismRegistry.summary returns correct structure
- validate_manifest passes on valid YAML
- validate_manifest raises on missing field
- validate_manifest raises on wrong type
```

---

## Prompt 2 — Registry Index

```
Build the registry system — the GitHub-backed JSON index that powers prism list and prism install.

---

PART A — registry/registry.json

The registry index. Initial content includes all five built-in connectors. Schema:

{
  "version": "1.0",
  "updated_at": "<ISO timestamp>",
  "connectors": [
    {
      "name": "Kalshi Fed Markets",
      "slug": "kalshi_fed",
      "version": "1.0.0",
      "author": "arpjw",
      "source_type": "prediction_market",
      "transport": "websocket",
      "description": "Streams KXFED contract prices from Kalshi via WebSocket.",
      "auth_required": true,
      "auth_fields": ["KALSHI_API_KEY", "KALSHI_PRIVATE_KEY_PATH"],
      "contract_slugs": ["KXFED"],
      "tags": ["fed", "rates", "macro", "kalshi"],
      "homepage": "https://github.com/arpjw/prism/tree/main/connectors/kalshi_fed.prism",
      "source_url": "https://github.com/arpjw/prism/archive/refs/heads/main.tar.gz",
      "source_path": "connectors/kalshi_fed.prism",
      "downloads": 0,
      "verified": true
    }
    // ... repeat for polymarket_macro, metaculus_macro, manifold_macro, fred_macro
  ]
}

All five built-in connectors must be present with accurate metadata.

---

PART B — registry/schema.json

JSON Schema (draft-07) for registry.json. Used by CI to validate PRs. Fields:
- version: string, required
- updated_at: string (ISO datetime), required
- connectors: array of connector objects, min 1 item

Each connector object schema — all fields from the example above with correct types, required fields marked, slug must match pattern ^[a-z][a-z0-9_]*$, version must match semver pattern.

---

PART C — CI: GitHub Actions

Create .github/workflows/validate_registry.yml:
  Triggers: pull_request (any branch), push to main

  Jobs:
  1. validate-registry:
     - Checkout repo
     - Validate registry/registry.json against registry/schema.json using jsonschema (pip install jsonschema)
     - Run python -m prism validate on every .prism package in connectors/
     - Report results

  2. validate-new-connectors:
     - Only runs on PRs
     - Detect which .prism packages were added or modified in the PR (git diff)
     - Run python -m prism validate on each changed package
     - Fail the PR if any validation check fails (not just warns)

Create .github/workflows/publish.yml:
  Triggers: push to main with tag matching v*.*.*

  Jobs:
  1. publish-pypi:
     - Build with hatchling: python -m build
     - Publish to PyPI using twine and PYPI_TOKEN secret
     - Create GitHub release with changelog

---

PART D — CONTRIBUTING_CONNECTORS.md (full rewrite for standalone repo)

Same 10 sections as the robinhood version but updated for the standalone context. Key differences:
- Section 2 Quickstart now starts with pip install prism-signal
- Section 9 Submitting covers the registry PR process specifically: fork arpjw/prism, add .prism package to connectors/, add entry to registry/registry.json, open PR. CI validates automatically.
- Add a new Section 10: Registry Entry — how to fill in registry.json for a new connector, what each field means, what "verified": true means (reviewed and tested by maintainer) vs false (community-submitted, use at your own risk).

---

PART E — Tests

tests/test_registry.py: at least 8 tests covering:
- registry.json is valid JSON
- registry.json passes schema validation
- All five built-in connectors are present in registry.json
- All slugs in registry.json are unique
- All source_urls are well-formed URLs
- RegistryClient.fetch returns parsed registry (mock HTTP)
- RegistryClient.find returns correct connector by slug
- RegistryClient.search filters by tag correctly
- Cache is written to ~/.prism/registry_cache.json
- Cache is used when network is unavailable
```

---

## Prompt 3 — Built-in Connectors Migration

```
Migrate all five built-in connectors from the robinhood project into the prism repo. Each must be a complete, standalone .prism package that works independently of the robinhood engine — the only dependency is prism-signal itself.

For each connector, the __init__.py must import from prism rather than from the robinhood project:
  from prism.base import PrismConnector, PrismMetadata, PricePoint
  from prism.velocity import VelocityTracker   # see note below

Since VelocityTracker lives in the robinhood project, create a minimal prism/velocity.py that contains only VelocityTracker and the types it needs (PricePoint, VelocitySignal). This is a copy-forward — extract just what connectors need without bringing in the rest of the signal engine.

Connectors to migrate (copy and adapt from robinhood):
1. connectors/kalshi_fed.prism/ — from signals/kalshi_poller.py
2. connectors/polymarket_macro.prism/ — from signals/polymarket_poller.py
3. connectors/metaculus_macro.prism/ — from connectors/metaculus_macro.prism/
4. connectors/manifold_macro.prism/ — from connectors/manifold_macro.prism/
5. connectors/fred_macro.prism/ — from connectors/fred_macro.prism/

Each migrated connector must:
- Import only from prism.base and prism.velocity (no robinhood imports)
- Have a complete connector.prism manifest
- Have a README.md with full documentation including auth setup, env vars, and example output
- Have at least 5 tests in its own tests/ subdirectory
- Pass prism validate with zero failures

Run prism validate on all five after migration. All must pass clean.

Add tests/test_connector_migration.py with at least 5 tests confirming each connector:
- Loads via PrismRegistry.load_directory
- Has metadata matching its connector.prism manifest
- Has no imports from the robinhood project
- Passes prism validate (invoke via subprocess)
```

---

## Prompt 4 — Marketplace UI

```
Build the Prism marketplace UI at ui/ as a Next.js 14 App Router project deployable to Vercel at prism.aryasomu.com.

---

DESIGN SYSTEM

Same Robinhood-inspired palette as the robinhood landing page — this is a sister project and should feel visually related but distinct. Key difference: the prism project gets a refraction motif — geometric light-splitting shapes, prismatic color hints on hover.

Colors:
  --bg: #080808                 # slightly darker than robinhood page
  --surface: #101010
  --surface-elevated: #181818
  --border: #202020
  --text-primary: #f0f0f0
  --text-secondary: #808080
  --text-tertiary: #484848
  --neon: #b3ff00               # Robin Neon — same as robinhood page
  --prism-blue: #00d4ff         # new accent for prism — electric cyan
  --prism-violet: #a855f7       # secondary prism accent
  --red: #ff4d4d

Typography: same as robinhood page — DM Serif Display, DM Mono, DM Sans from Google Fonts.

---

PAGES

app/page.tsx — Home / Registry Browser

Header (fixed, same structure as robinhood page):
  Left: "PRISM" in DM Mono, letter-spacing 0.2em. A small geometric prism SVG icon to the left (triangle with a refraction line).
  Right: "GitHub", "Docs", "arpjw" links.

Hero section:
  Full-width, not full-height. Padding 96px 0 64px.
  
  Left column (60%):
  - Eyebrow: "CONNECTOR REGISTRY v1.0" in DM Mono 11px --neon
  - Headline: "Any signal source." DM Serif Display 56px.
  - Second line: "One interface." in --prism-blue. 400ms stagger fade-up.
  - Body: "Prism is an open connector format for velocity signal engines. Browse community connectors, install with one command, or build your own in minutes." DM Sans 17px --text-secondary.
  - Two stat pills below (DM Mono 13px, background --surface, border --border, border-radius 100px, padding 8px 16px):
    "5 connectors" and "pip install prism-signal"
    The pip install pill has a copy-to-clipboard button (small icon, copies "pip install prism-signal" on click).
  
  Right column (40%):
  - A terminal showing prism list --registry output as a styled pre block, same terminal widget aesthetic as robinhood page. Static content is fine — no live fetch needed here.

Registry section (main content, below hero):
  
  Filter bar: full width, sticky below header when scrolling.
    - Search input: "Search connectors..." placeholder, DM Mono 13px, background --surface, border --border.
    - Filter pills: "All", "Prediction Market", "Alternative Data", "News", "Custom" — DM Mono 11px.
    - Transport filter: "All", "WebSocket", "REST", "Push"
    - Sort: "Most Downloaded", "Newest", "A-Z"
    - Background: rgba(8,8,8,0.9) backdrop-filter blur(12px). Border-bottom --border.

  Connector grid: 3-col desktop, 2-col tablet, 1-col mobile. Gap 16px.

  ConnectorCard component (for each connector in registry.json):
    - Background --surface, border 1px solid --border, border-radius 8px, padding 24px.
    - On hover: border --neon (for verified), border --prism-blue (for unverified community).
    - Top row: connector name (DM Serif Display 18px) + verified badge if verified: true (small checkmark + "VERIFIED" in DM Mono 10px --neon).
    - Slug in DM Mono 12px --text-tertiary below name.
    - Description: DM Sans 14px --text-secondary, 2-line clamp with ellipsis.
    - Tags: small pills, DM Mono 10px, background #1a1a1a, --text-secondary.
    - Bottom row: transport badge (WS/REST/PUSH in DM Mono 10px --neon bg), auth badge (AUTH/PUBLIC), author in DM Mono 11px --text-tertiary.
    - Install command: "prism install {slug}" in DM Mono 12px --text-tertiary. Copy icon on hover.

  Data: fetch registry.json from GitHub raw URL on page load. Show skeleton loaders while fetching. If fetch fails, show inline error with retry button.

  Filtering and search: client-side, no backend needed — filter the fetched registry array in memory.

app/connector/[slug]/page.tsx — Connector Detail Page

  Route: /connector/{slug}
  Data: fetch registry.json, find connector by slug. If not found, 404.
  
  Layout: single column, max-width 800px, centered.
  
  Header breadcrumb: "PRISM / {slug}" in DM Mono 13px.
  
  Hero: connector name in DM Serif Display 42px, description below, badges row (transport, source_type, auth, verified).
  
  Install section: styled code block showing:
    pip install prism-signal
    prism install {slug}
  Copy button for each line.
  
  Details sections (use a left-border card pattern — 3px left border in --neon, background --surface, padding 20px 24px):
  - Auth Required: list each auth_field with a brief description
  - Contract Slugs: which prediction market contracts this connector maps to
  - Configuration: env vars (pulled from README if parseable, otherwise placeholder)
  - Tags: all tags as pills
  
  README section: show connector README.md content below. Fetch from GitHub raw URL using the source_path from registry.json. Render as styled markdown (implement a minimal markdown renderer for headers, paragraphs, code blocks, and lists — no external library).
  
  Back link: "← Back to registry" at top and bottom.

app/docs/page.tsx — Documentation

  Single page pulling content from CONTRIBUTING_CONNECTORS.md. Fetch from GitHub raw URL. Render as styled markdown. Left sidebar navigation generated from ## headers. Sticky sidebar on desktop.

app/layout.tsx — shared layout with Header and Footer.

Footer: same three-column pattern as robinhood page. Center: "prism-signal on PyPI", links to GitHub and arpjw.com.

---

COMPONENTS

ConnectorCard.tsx — grid card (described above)
TerminalBlock.tsx — reusable styled terminal widget (title bar with dots, monospace content)
CopyButton.tsx — copy-to-clipboard with visual feedback (text changes to "Copied!" for 2s)
MarkdownRenderer.tsx — minimal markdown renderer (no external library): handles h1/h2/h3, p, code blocks (with DM Mono styling), ul/ol/li, strong/em, links. Code blocks get a copy button.
SkeletonCard.tsx — loading skeleton for ConnectorCard with pulse animation
FilterBar.tsx — search + filter pills + sort

---

TECHNICAL

Same constraints as robinhood UI: no Tailwind, no component libraries, CSS variables, DM fonts from Google Fonts. TypeScript.

All data fetching uses the registry.json GitHub raw URL — no backend, no API routes needed.

Include a vercel.json at ui/ root with:
{
  "rewrites": [{ "source": "/(.*)", "destination": "/" }]
}
for client-side routing support.

Include README with: npm install && npm run dev, and Vercel deployment instructions (root directory: ui, custom domain: prism.aryasomu.com).
```

---

## Prompt 5 — README and Package Polish

```
Final polish pass before the first public release.

---

README.md (repo root)

Sections in order:

1. Header: "PRISM" in large text, one-line description, badges (PyPI version, license MIT, tests passing).

2. What is Prism? (3 paragraphs):
   - The problem: velocity signal engines need a standard way to ingest data from heterogeneous sources. Without a common interface, every engine reimplements the same polling, auth, and normalization logic.
   - The solution: .prism is a self-contained connector format. Any data source that produces a time series can be a connector. The PrismConnector interface handles the contract; the developer handles the source.
   - The ecosystem: a GitHub-backed registry of community connectors, installable with one command.

3. Quickstart (5 commands):
   pip install prism-signal
   prism list --registry
   prism install kalshi_fed
   prism scaffold --name "My Source" --slug my_source --type prediction_market --transport rest
   prism validate connectors/my_source.prism

4. Built-in connectors table: name, slug, source, transport, auth, tags.

5. CLI reference: one-line description of each command with usage example.

6. The .prism format: directory structure, connector.prism schema table (field, type, required, description).

7. PrismConnector interface: the three abstract methods with signatures and what each must do.

8. The PricePoint contract: fields table, normalization requirement, example.

9. Contributing a connector: three sentences + link to CONTRIBUTING_CONNECTORS.md.

10. License: MIT.

---

pyproject.toml final polish:
  - Add classifiers: "Development Status :: 3 - Alpha", "Intended Audience :: Developers", "Topic :: Office/Business :: Financial :: Investment", "Programming Language :: Python :: 3.11", "License :: OSI Approved :: MIT License"
  - Add [project.urls]: Homepage, Repository, Documentation, "Bug Tracker"
  - Add [tool.hatch.version] pointing to prism/__init__.py for single-source versioning
  - Set __version__ = "0.1.0" in prism/__init__.py

LICENSE: MIT, copyright Arya Somu 2026.

.github/PULL_REQUEST_TEMPLATE.md for connector submissions:
  ## Connector submission checklist
  - [ ] connector.prism manifest is complete
  - [ ] prism validate passes with zero failures
  - [ ] README.md documents all auth_fields and env vars
  - [ ] At least 5 tests in tests/
  - [ ] registry/registry.json entry added
  - [ ] I have tested this connector against a live data source

Final test run: pytest tests/ -q. Target: 60+ tests passing across all test files.

Verify the full CLI works end-to-end:
  pip install -e .
  prism version
  prism scaffold --name "Test" --slug test_conn --type custom --transport rest
  prism validate connectors/test_conn.prism
  prism list --registry
```

---

## Deployment

After all 5 prompts:

1. Push to github.com/arpjw/prism
2. Deploy UI to Vercel — root directory: ui, custom domain: prism.aryasomu.com
3. Add CNAME record in Wix DNS: prism → cname.vercel-dns.com
4. Publish to PyPI:
   pip install build twine
   python -m build
   twine upload dist/*
5. Add PYPI_TOKEN secret to GitHub repo settings for the publish workflow

---

## Notes

- The prism repo is fully independent — zero imports from the robinhood repo
- prism/velocity.py is a copy-forward of just VelocityTracker — keep it minimal
- The registry.json is the source of truth — the UI reads it, the CLI reads it, CI validates it
- "verified": true means the connector has been reviewed by the maintainer. Community submissions default to false.
- Do not implement download counting yet — the downloads field in registry.json is a placeholder for when a backend exists
- The UI should work entirely without a backend — all data comes from GitHub raw URLs
- Run prism validate on all five built-in connectors before considering any prompt complete
