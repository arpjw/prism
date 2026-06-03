# Metaculus Macro

Polls macro forecasting questions from the Metaculus REST API.

## Overview

This connector polls the Metaculus REST API every 60 seconds for the community forecast on
macro-related questions (Fed funds rate, US recession probability). Metaculus questions produce
calibrated probability forecasts from a community of superforecasters.

## Auth

No authentication required. Metaculus's public API is open.

## Config

No configuration required. Poll interval is 60 seconds (hardcoded).

## Emitted Signals

| Contract Slug | Description | Metaculus Question ID |
|---------------|-------------|----------------------|
| fed-funds-rate-2026 | Will the Fed funds rate be above X% by end of 2026? | 14750 |
| us-recession-2026 | Will the US enter a recession in 2026? | 11560 |

## Normalization

Metaculus community predictions are already probabilities in [0.0, 1.0]. The `q2` (median) of
the community distribution is used as the price.

## Example Output

```
PricePoint(timestamp=2026-01-01T00:00:00+00:00, price=0.35, volume=287, slug="us-recession-2026", source="metaculus_macro")
```

## Installation

```bash
pip install prism-signal
prism install metaculus_macro
```
