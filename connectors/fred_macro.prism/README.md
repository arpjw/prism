# FRED Macro

Polls Federal Reserve Economic Data (FRED) series and normalizes values to [0, 1].

## Overview

This connector polls the FRED REST API every 300 seconds for the latest observations of
key Fed-related economic series. Raw rate values are normalized to [0.0, 1.0] using fixed bounds
(0% to 10%), making them compatible with the Prism PricePoint format.

## Auth

| Env Var | Required | Description |
|---------|----------|-------------|
| FRED_API_KEY | Yes | Your FRED API key from https://fred.stlouisfed.org/docs/api/api_key.html |

Set before running:

```bash
export FRED_API_KEY=your_fred_api_key_here
```

A free FRED API key can be obtained at: https://fred.stlouisfed.org/docs/api/api_key.html

## Config

Poll interval: 300 seconds (5 minutes, matching FRED's update frequency).

## Emitted Signals

| Contract Slug | Series | Description | Normalization |
|---------------|--------|-------------|---------------|
| FEDFUNDS | FEDFUNDS | Effective Federal Funds Rate (monthly avg) | value / 10.0 |
| DFF | DFF | Daily Federal Funds Rate | value / 10.0 |
| EFFR | EFFR | Effective Federal Funds Rate (SOFR-adjacent) | value / 10.0 |

## Normalization Formula

```
price = clamp((value - 0.0) / (10.0 - 0.0), 0.0, 1.0)
```

At 5.25% fed funds rate: price = 0.525

## Example Output

```
PricePoint(timestamp=2026-01-01T00:00:00+00:00, price=0.525, volume=0, slug="FEDFUNDS", source="fred_macro")
PricePoint(timestamp=2026-01-01T00:00:00+00:00, price=0.532, volume=0, slug="DFF", source="fred_macro")
```

## Installation

```bash
pip install prism-signal
prism install fred_macro
```
