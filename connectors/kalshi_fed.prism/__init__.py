"""Kalshi Fed Markets connector. Streams KXFED contract prices via WebSocket."""
from __future__ import annotations
import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Callable

from prism.base import PrismConnector, PrismMetadata, PricePoint

logger = logging.getLogger(__name__)

KALSHI_WS_URL = "wss://trading-api.kalshi.com/trade-api/ws/v2"
TICKER_SERIES = "KXFED"


class KalshiFedConnector(PrismConnector):
    """Streams KXFED prediction market prices from Kalshi via WebSocket."""

    metadata = PrismMetadata(
        name="Kalshi Fed Markets",
        slug="kalshi_fed",
        version="1.0.0",
        author="arpjw",
        source_type="prediction_market",
        transport="websocket",
        description="Streams KXFED contract prices from Kalshi via WebSocket.",
        auth_required=True,
        auth_fields=["KALSHI_API_KEY", "KALSHI_PRIVATE_KEY_PATH"],
        contract_slugs=["KXFED"],
        tags=["fed", "rates", "macro", "kalshi"],
        homepage="https://github.com/arpjw/prism/tree/main/connectors/kalshi_fed.prism",
    )

    def __init__(self, on_price: Callable[[PricePoint], None] | None = None):
        self._on_price = on_price
        self._running = False
        self._ws = None
        self._task: asyncio.Task | None = None
        self._api_key = os.environ.get("KALSHI_API_KEY", "")
        self._key_path = os.environ.get("KALSHI_PRIVATE_KEY_PATH", "")

    async def start(self) -> None:
        """Open Kalshi WebSocket and begin streaming KXFED prices."""
        if not self._api_key:
            raise RuntimeError("KALSHI_API_KEY environment variable not set")
        self._running = True
        self._task = asyncio.create_task(self._stream())

    async def stop(self) -> None:
        """Gracefully close the WebSocket connection."""
        self._running = False
        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception:
                pass
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def health_check(self) -> bool:
        """Return True if the WebSocket task is alive and running."""
        if not self._running:
            return False
        if self._task is not None and self._task.done():
            return False
        return True

    async def _stream(self) -> None:
        try:
            import websockets
            async with websockets.connect(
                KALSHI_WS_URL,
                extra_headers={"Authorization": f"Bearer {self._api_key}"},
            ) as ws:
                self._ws = ws
                await ws.send(json.dumps({
                    "id": 1,
                    "cmd": "subscribe",
                    "params": {
                        "channels": ["ticker"],
                        "market_tickers": [TICKER_SERIES],
                    },
                }))
                async for raw in ws:
                    if not self._running:
                        break
                    try:
                        msg = json.loads(raw)
                        self._handle_message(msg)
                    except Exception as e:
                        logger.warning("Failed to parse message: %s", e)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("KalshiFedConnector stream error: %s", e)
            self._running = False

    def _handle_message(self, msg: dict) -> None:
        data = msg.get("msg", msg)
        msg_type = msg.get("type") or data.get("type")
        if msg_type == "ticker" and "yes_bid" in data:
            try:
                raw_price = float(data["yes_bid"]) / 100.0
                price = max(0.0, min(1.0, raw_price))
                pt = PricePoint(
                    timestamp=datetime.now(timezone.utc),
                    price=price,
                    volume=int(data.get("volume", 0)),
                    slug=data.get("market_ticker", TICKER_SERIES),
                    source="kalshi_fed",
                )
                if self._on_price is not None:
                    self._on_price(pt)
            except Exception as e:
                logger.warning("Failed to create PricePoint: %s", e)
