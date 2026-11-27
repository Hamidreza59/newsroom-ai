"""In-memory TTL cache with one in-flight load per key."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any


class TTLCache:
    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self.clock = clock
        self.entries: dict[str, tuple[float, datetime, Any]] = {}
        self.locks: dict[str, asyncio.Lock] = {}

    async def get(self, key: str, ttl: float,
                  loader: Callable[[], Awaitable[Any]]) -> tuple[Any, datetime]:
        """Cached value and the time it was loaded."""
        entry = self.entries.get(key)
        if entry and entry[0] > self.clock():
            return entry[2], entry[1]
        async with self.locks.setdefault(key, asyncio.Lock()):
            entry = self.entries.get(key)
            if entry and entry[0] > self.clock():
                return entry[2], entry[1]
            value = await loader()
            loaded = datetime.now(UTC)
            self.entries[key] = (self.clock() + ttl, loaded, value)
            return value, loaded
