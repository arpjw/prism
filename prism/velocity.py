from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from datetime import datetime

from prism.base import PricePoint


@dataclass
class VelocitySignal:
    slug: str
    velocity: float
    acceleration: float
    timestamp: datetime
    sample_count: int
    price_latest: float
    price_oldest: float


class VelocityTracker:
    """Computes velocity and acceleration for a streaming price series."""

    def __init__(self, window_seconds: float = 60.0, min_samples: int = 2):
        self.window_seconds = window_seconds
        self.min_samples = min_samples
        self._buffers: dict[str, deque[PricePoint]] = {}

    def push(self, point: PricePoint) -> VelocitySignal | None:
        slug = point.slug or point.source
        if slug not in self._buffers:
            self._buffers[slug] = deque()
        buf = self._buffers[slug]
        buf.append(point)
        cutoff = point.timestamp.timestamp() - self.window_seconds
        while buf and buf[0].timestamp.timestamp() < cutoff:
            buf.popleft()
        if len(buf) < self.min_samples:
            return None
        return self._compute(slug, buf, point.timestamp)

    def _compute(self, slug: str, buf: deque[PricePoint], now: datetime) -> VelocitySignal:
        points = list(buf)
        t0 = points[0].timestamp.timestamp()
        t1 = points[-1].timestamp.timestamp()
        dt = t1 - t0 if t1 != t0 else 1e-9
        velocity = (points[-1].price - points[0].price) / dt
        mid = len(points) // 2
        if mid > 0:
            dt_first = points[mid].timestamp.timestamp() - points[0].timestamp.timestamp() or 1e-9
            dt_second = points[-1].timestamp.timestamp() - points[mid].timestamp.timestamp() or 1e-9
            v_first = (points[mid].price - points[0].price) / dt_first
            v_second = (points[-1].price - points[mid].price) / dt_second
            acceleration = (v_second - v_first) / ((dt_first + dt_second) / 2 or 1e-9)
        else:
            acceleration = 0.0
        return VelocitySignal(
            slug=slug,
            velocity=velocity,
            acceleration=acceleration,
            timestamp=now,
            sample_count=len(points),
            price_latest=points[-1].price,
            price_oldest=points[0].price,
        )
