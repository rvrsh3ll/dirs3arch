from __future__ import annotations

import asyncio
import threading
import time
from collections import deque
from collections.abc import Awaitable, Callable


RATE_WINDOW_SECONDS = 1.0
RATE_WAIT_POLL_SECONDS = 0.1


class RequestRateLimiter:
    def __init__(
        self,
        clock: Callable[[], float] | None = None,
        sleep: Callable[[float], None] | None = None,
        async_sleep: Callable[[float], Awaitable[None]] | None = None,
    ) -> None:
        self._clock = clock or time.monotonic
        self._sleep = sleep or time.sleep
        self._async_sleep = async_sleep or asyncio.sleep
        self._request_times: deque[float] = deque()
        self._lock = threading.Lock()

    def wait(self, max_rate: int) -> None:
        while (delay := self._reserve(max_rate)) is not None:
            self._sleep(min(delay, RATE_WAIT_POLL_SECONDS))

    async def wait_async(self, max_rate: int) -> None:
        while (delay := self._reserve(max_rate)) is not None:
            await self._async_sleep(min(delay, RATE_WAIT_POLL_SECONDS))

    @property
    def rate(self) -> int:
        with self._lock:
            self._discard_expired(self._clock())
            return len(self._request_times)

    def _reserve(self, max_rate: int) -> float | None:
        with self._lock:
            now = self._clock()
            self._discard_expired(now)
            if max_rate <= 0 or len(self._request_times) < max_rate:
                self._request_times.append(now)
                return None

            return max(
                0.0,
                self._request_times[0] + RATE_WINDOW_SECONDS - now,
            )

    def _discard_expired(self, now: float) -> None:
        cutoff = now - RATE_WINDOW_SECONDS
        while self._request_times and self._request_times[0] <= cutoff:
            self._request_times.popleft()
