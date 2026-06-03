"""Polymarket Macro connector. Streams macro market prices from Polymarket via WebSocket."""
from __future__ import annotations
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Callable

from prism.base import PrismConnector, PrismMetadata, PricePoint

logger = logging.getLogger(__name__)

POLYMARKET_WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

MARKET_SLUGS = [
    "will-the-fed-cut-rates-in-2026",
    "will-the-fed-raise-rates-in-2026",
]


class PolymarketMacroConnector(PrismConnector):
    """Streams macro prediction market prices from Polymarket via WebSocket."""

    metadata = PrismMetadata(
        name="Polymarket Macro",
        slug="polymarket_macro",
        version="1.0.0",
        author="arpjw",
        source_type="prediction_market",
        transport="websocket",
        description="Streams macro-related prediction market prices from Polymarket via WebSocket.",
        auth_required=False,
        auth_fields=[],
        contract_slugs=[
            "will-the-fed-cut-rates-in-2026",
            "will-the-fed-raise-rates-in-2026",
        ],
        tags=["fed", "rates", "macro", "polymarket"],
        homepage="https://github.com/arpjw/prism/tree/main/connectors/polymarket_macro.prism",
    )

    def __init__(self, on_price: Callable[[PricePoint], None] | None = None):
        self._on_price = on_price
        self._running = False
        self._ws = None
        self._task: asyncio.Task | None = None
        self._last_prices: dict[str, float] = {}

    async def start(self) -> None:
        """Open Polymarket WebSocket and begin streaming macro market prices."""
        self._running = True
        self._task = asyncio.create_task(self._stream())

    async def stop(self) -> None:
        """Close the Polymarket WebSocket connection."""
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
        """Return True if the stream is active."""
        if not self._running:
            return False
        if self._task is not None and self._task.done():
            return False
        return True

    async def _stream(self) -> None:
        try:
            import websockets
            async with websockets.connect(POLYMARKET_WS_URL) as ws:
                self._ws = ws
                # Subscribe to price updates for our markets
                await ws.send(json.dumps({
                    "type": "subscribe",
                    "channel": "market",
                    "markets": MARKET_SLUGS,
                }))
                async for raw in ws:
                    if not self._running:
                        break
                    try:
                        msg = json.loads(raw)
                        self._handle_message(msg)
                    except Exception as e:
                        logger.warning("Failed to parse Polymarket message: %s", e)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("PolymarketMacroConnector stream error: %s", e)
            self._running = False

    def _handle_message(self, msg: dict) -> None:
        # Polymarket CLOB WebSocket sends price_change events
        event_type = msg.get("event_type") or msg.get("type")
        if event_type in ("price_change", "book"):
            market_slug = msg.get("market", "")
            price_str = msg.get("price") or msg.get("best_ask") or msg.get("midpoint")
            if price_str is None:
                return
            try:
                price = float(price_str)
                price = max(0.0, min(1.0, price))
                self._last_prices[market_slug] = price
                pt = PricePoint(
                    timestamp=datetime.now(timezone.utc),
                    price=price,
                    volume=int(msg.get("size", 0)),
                    slug=market_slug,
                    source="polymarket_macro",
                )
                if self._on_price is not None:
                    self._on_price(pt)
            except (ValueError, TypeError) as e:
                logger.warning("Failed to parse Polymarket price: %s", e)
