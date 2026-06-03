"""Metaculus Macro connector. Polls macro forecasting questions from Metaculus REST API."""
from __future__ import annotations
import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Callable

import httpx

from prism.base import PrismConnector, PrismMetadata, PricePoint

logger = logging.getLogger(__name__)

METACULUS_API_URL = "https://www.metaculus.com/api2/questions/"
POLL_INTERVAL = 60.0

# Map contract slug → Metaculus question ID
QUESTION_IDS: dict[str, int] = {
    "fed-funds-rate-2026": 14750,
    "us-recession-2026": 11560,
}


class MetaculusMacroConnector(PrismConnector):
    """Polls macro forecasting questions from the Metaculus REST API."""

    metadata = PrismMetadata(
        name="Metaculus Macro",
        slug="metaculus_macro",
        version="1.0.0",
        author="arpjw",
        source_type="prediction_market",
        transport="rest",
        description="Polls macro forecasting questions from Metaculus REST API.",
        auth_required=False,
        auth_fields=[],
        contract_slugs=["fed-funds-rate-2026", "us-recession-2026"],
        tags=["fed", "macro", "forecasting", "metaculus"],
        homepage="https://github.com/arpjw/prism/tree/main/connectors/metaculus_macro.prism",
    )

    def __init__(self, on_price: Callable[[PricePoint], None] | None = None):
        self._on_price = on_price
        self._running = False
        self._task: asyncio.Task | None = None
        self._last_poll: float = 0.0

    async def start(self) -> None:
        """Start polling Metaculus questions every 60 seconds."""
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
        """Return True if the last successful poll was within 120 seconds."""
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
                logger.error("Metaculus poll error: %s", e)
            await asyncio.sleep(POLL_INTERVAL)

    async def _fetch_all(self) -> None:
        async with httpx.AsyncClient(timeout=15.0) as client:
            for slug, question_id in QUESTION_IDS.items():
                try:
                    resp = await client.get(f"{METACULUS_API_URL}{question_id}/")
                    resp.raise_for_status()
                    data = resp.json()
                    probability = self._extract_probability(data)
                    if probability is not None:
                        pt = PricePoint(
                            timestamp=datetime.now(timezone.utc),
                            price=max(0.0, min(1.0, probability)),
                            volume=int(data.get("number_of_predictions", 0)),
                            slug=slug,
                            source="metaculus_macro",
                        )
                        if self._on_price is not None:
                            self._on_price(pt)
                except Exception as e:
                    logger.warning("Failed to fetch Metaculus question %d (%s): %s", question_id, slug, e)

    def _extract_probability(self, data: dict) -> float | None:
        # Metaculus returns community_prediction.full.q2 or prediction for binary questions
        community = data.get("community_prediction") or {}
        full = community.get("full") or {}
        if "q2" in full:
            return float(full["q2"])
        prediction = data.get("prediction")
        if prediction is not None:
            return float(prediction)
        return None
