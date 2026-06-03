"""FRED Macro connector. Polls Federal Reserve Economic Data series."""
from __future__ import annotations
import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from typing import Callable

import httpx

from prism.base import PrismConnector, PrismMetadata, PricePoint

logger = logging.getLogger(__name__)

FRED_API_URL = "https://api.stlouisfed.org/fred/series/observations"
POLL_INTERVAL = 300.0

# Normalization bounds for each series: price = (value - min) / (max - min)
SERIES_BOUNDS: dict[str, tuple[float, float]] = {
    "FEDFUNDS": (0.0, 10.0),
    "DFF": (0.0, 10.0),
    "EFFR": (0.0, 10.0),
}


class FredMacroConnector(PrismConnector):
    """Polls FRED economic series and normalizes values to [0, 1]."""

    metadata = PrismMetadata(
        name="FRED Macro",
        slug="fred_macro",
        version="1.0.0",
        author="arpjw",
        source_type="alternative_data",
        transport="rest",
        description="Polls Federal Reserve Economic Data (FRED) series and normalizes to [0,1] for use as signal inputs.",
        auth_required=True,
        auth_fields=["FRED_API_KEY"],
        contract_slugs=["FEDFUNDS", "DFF", "EFFR"],
        tags=["fed", "rates", "macro", "economic-data", "fred"],
        homepage="https://github.com/arpjw/prism/tree/main/connectors/fred_macro.prism",
    )

    def __init__(self, on_price: Callable[[PricePoint], None] | None = None):
        self._on_price = on_price
        self._running = False
        self._task: asyncio.Task | None = None
        self._last_poll: float = 0.0
        self._api_key: str = os.environ.get("FRED_API_KEY", "")

    async def start(self) -> None:
        """Start polling FRED series every 300 seconds."""
        if not self._api_key:
            raise RuntimeError("FRED_API_KEY environment variable not set")
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
        """Return True if the last poll was within 600 seconds."""
        if not self._running:
            return False
        if self._task is not None and self._task.done():
            return False
        return (time.monotonic() - self._last_poll) < 600.0

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                await self._fetch_all()
                self._last_poll = time.monotonic()
            except Exception as e:
                logger.error("FRED poll error: %s", e)
            await asyncio.sleep(POLL_INTERVAL)

    async def _fetch_all(self) -> None:
        async with httpx.AsyncClient(timeout=15.0) as client:
            for series_id, (min_val, max_val) in SERIES_BOUNDS.items():
                try:
                    resp = await client.get(FRED_API_URL, params={
                        "series_id": series_id,
                        "api_key": self._api_key,
                        "file_type": "json",
                        "sort_order": "desc",
                        "limit": 1,
                    })
                    resp.raise_for_status()
                    data = resp.json()
                    observations = data.get("observations", [])
                    if not observations:
                        continue
                    latest = observations[0]
                    value_str = latest.get("value", ".")
                    if value_str == ".":
                        continue
                    value = float(value_str)
                    price = (value - min_val) / (max_val - min_val)
                    price = max(0.0, min(1.0, price))
                    pt = PricePoint(
                        timestamp=datetime.now(timezone.utc),
                        price=price,
                        volume=0,
                        slug=series_id,
                        source="fred_macro",
                    )
                    if self._on_price is not None:
                        self._on_price(pt)
                except Exception as e:
                    logger.warning("Failed to fetch FRED series %s: %s", series_id, e)
