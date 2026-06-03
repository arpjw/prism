# Kalshi Fed Markets

Streams KXFED contract prices from Kalshi via WebSocket.

## Overview

This connector subscribes to the Kalshi WebSocket API and streams real-time yes-bid prices for
KXFED contracts (Federal Reserve interest rate decision markets). Prices are normalized to [0.0, 1.0]
by dividing the raw cent-price by 100.

## Auth

| Env Var | Required | Description |
|---------|----------|-------------|
| KALSHI_API_KEY | Yes | Your Kalshi API key from the Kalshi trading dashboard |
| KALSHI_PRIVATE_KEY_PATH | Yes | Path to your RSA private key file for Kalshi API authentication |

Set these before running:

```bash
export KALSHI_API_KEY=your_api_key_here
export KALSHI_PRIVATE_KEY_PATH=/path/to/your/private_key.pem
```

## Config

No additional configuration required beyond auth fields.

## Emitted Signals

| Contract Slug | Description |
|---------------|-------------|
| KXFED | Kalshi Federal Reserve rate decision market |

## Normalization

Raw Kalshi prices are in cents (0–100). This connector divides by 100 to produce a [0.0, 1.0] probability.

## Example Output

```
PricePoint(timestamp=2026-01-01T00:00:00+00:00, price=0.72, volume=1500, slug="KXFED", source="kalshi_fed")
```

## Installation

```bash
pip install prism-signal
prism install kalshi_fed
```

## Usage

```python
from connectors.kalshi_fed.prism import KalshiFedConnector
import asyncio

def on_price(pt):
    print(f"{pt.slug}: {pt.price:.3f} @ {pt.timestamp}")

async def main():
    conn = KalshiFedConnector(on_price=on_price)
    await conn.start()
    await asyncio.sleep(60)
    await conn.stop()

asyncio.run(main())
```
