# Polymarket Macro

Streams macro-related prediction market prices from Polymarket via WebSocket.

## Overview

This connector subscribes to the Polymarket CLOB WebSocket API and streams real-time prices
for macro prediction markets (Fed rate decisions, inflation, recession). No authentication required —
Polymarket's data is publicly accessible.

## Auth

No authentication required. Polymarket's CLOB WebSocket is public.

## Config

No configuration required.

## Emitted Signals

| Contract Slug | Description |
|---------------|-------------|
| will-the-fed-cut-rates-in-2026 | Probability the Fed cuts rates at least once in 2026 |
| will-the-fed-raise-rates-in-2026 | Probability the Fed raises rates at least once in 2026 |

## Normalization

Polymarket prices are already in [0.0, 1.0] representing the yes probability. No transformation needed.

## Example Output

```
PricePoint(timestamp=2026-01-01T00:00:00+00:00, price=0.68, volume=50000, slug="will-the-fed-cut-rates-in-2026", source="polymarket_macro")
```

## Installation

```bash
pip install prism-signal
prism install polymarket_macro
```
