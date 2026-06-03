# Manifold Macro

Polls macro-tagged prediction markets from Manifold Markets REST API.

## Overview

This connector polls the Manifold Markets REST API every 60 seconds for macro-related prediction
markets. Manifold uses a play-money prediction market system with well-calibrated community forecasts.

## Auth

No authentication required. Manifold's public API is open.

## Config

No configuration required. Poll interval is 60 seconds (hardcoded).

## Emitted Signals

| Contract Slug | Description |
|---------------|-------------|
| will-the-fed-cut-rates-before-2027 | Probability the Fed cuts rates before Jan 1, 2027 |

## Normalization

Manifold `probability` field is already in [0.0, 1.0]. Used directly as PricePoint price.

## Example Output

```
PricePoint(timestamp=2026-01-01T00:00:00+00:00, price=0.74, volume=1200, slug="will-the-fed-cut-rates-before-2027", source="manifold_macro")
```

## Installation

```bash
pip install prism-signal
prism install manifold_macro
```
