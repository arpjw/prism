"""Manifold Macro connector. Polls macro-tagged markets from Manifold Markets REST API."""
from __future__ import annotations
import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Callable

import httpx

from prism.base import PrismConnector, PrismMetadata, PricePoint

logger = logging.getLogger(__name__)

MANIFOLD_API_URL = "https://api.manifold.markets/v0"
POLL_INTERVAL = 60.0

TARGET_SLUGS = [
    "will-the-fed-cut-rates-before-2027",
]


class ManifoldMacroConnector(PrismConnector):
    """Polls macro-tagged prediction markets from Manifold Markets REST API."""

    metadata = PrismMetadata(
        name="Manifold Macro",
        slug="manifold_macro",
        version="1.0.0",
        author="arpjw",
        source_type="prediction_market",
        transport="rest",
        description="Polls macro-tagged prediction markets from Manifold Markets REST API.",
        auth_required=False,
        auth_fields=[],
        contract_slugs=["will-the-fed-cut-rates-before-2027"],
        tags=["fed", "macro", "manifold"],
        homepage="https://github.com/arpjw/prism/tree/main/connectors/manifold_macro.prism",
    )

    def __init__(self, on_price: Callable[[PricePoint], None] | None = None):
        self._on_price = on_price
        self._running = False
        self._task: asyncio.Task | None = None
        self._last_poll: float = 0.0

    async def start(self) -> None:
        """Start polling Manifold macro markets every 60 seconds."""
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        """Stop the polling loop."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def health_check(self) -> bool:
        """Return True if the last poll was within 120 seconds."""
        if not self._running:
            return False
        if self._task is not None and self._task.done():
            return False
        return (time.monotonic() - self._last_poll) < 120.0

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                await self._fetch_all()
                self._last_poll = time.monotonic()
            except Exception as e:
                logger.error("Manifold poll error: %s", e)
            await asyncio.sleep(POLL_INTERVAL)

    async def _fetch_all(self) -> None:
        async with httpx.AsyncClient(timeout=15.0) as client:
            for slug in TARGET_SLUGS:
                try:
                    resp = await client.get(f"{MANIFOLD_API_URL}/slug/{slug}")
                    resp.raise_for_status()
                    data = resp.json()
                    probability = data.get("probability")
                    if probability is not None:
                        price = max(0.0, min(1.0, float(probability)))
                        pt = PricePoint(
                            timestamp=datetime.now(timezone.utc),
                            price=price,
                            volume=int(data.get("volume", 0)),
                            slug=slug,
                            source="manifold_macro",
                        )
                        if self._on_price is not None:
                            self._on_price(pt)
                except Exception as e:
                    logger.warning("Failed to fetch Manifold market %s: %s", slug, e)
