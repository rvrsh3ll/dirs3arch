import threading
from unittest import IsolatedAsyncioTestCase, TestCase

from lib.connection.rate_limiter import RequestRateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps = []

    def __call__(self) -> float:
        return self.now

    def sleep(self, delay: float) -> None:
        self.sleeps.append(delay)
        self.now += delay

    async def sleep_async(self, delay: float) -> None:
        self.sleep(delay)


class ControlledClock:
    def __init__(self) -> None:
        self._now = 0.0
        self._lock = threading.Lock()

    def __call__(self) -> float:
        with self._lock:
            return self._now

    def set(self, value: float) -> None:
        with self._lock:
            self._now = value


class ControlledSleeper:
    def __init__(self) -> None:
        self._calls = 0
        self._lock = threading.Lock()
        self.first_waiters_ready = threading.Event()
        self.release_first_waiters = threading.Event()
        self.second_waiter_ready = threading.Event()
        self.release_second_waiter = threading.Event()

    def __call__(self, _delay: float) -> None:
        with self._lock:
            self._calls += 1
            call = self._calls
            if call == 2:
                self.first_waiters_ready.set()
            elif call == 3:
                self.second_waiter_ready.set()

        release = (
            self.release_first_waiters
            if call <= 2
            else self.release_second_waiter
        )
        if not release.wait(timeout=1):
            raise RuntimeError("rate limiter test sleeper was not released")


class TestRequestRateLimiter(TestCase):
    def test_unlimited_requests_are_recorded_without_sleeping(self):
        clock = FakeClock()
        limiter = RequestRateLimiter(clock=clock, sleep=clock.sleep)

        for _ in range(3):
            limiter.wait(max_rate=0)

        self.assertEqual(clock.sleeps, [])
        self.assertEqual(limiter.rate, 3)

    def test_sync_wait_uses_a_rolling_one_second_window(self):
        clock = FakeClock()
        limiter = RequestRateLimiter(clock=clock, sleep=clock.sleep)

        limiter.wait(max_rate=2)
        limiter.wait(max_rate=2)
        limiter.wait(max_rate=2)

        self.assertAlmostEqual(clock.now, 1.0)
        self.assertEqual(limiter.rate, 1)

    def test_expired_requests_leave_the_reported_rate(self):
        clock = FakeClock()
        limiter = RequestRateLimiter(clock=clock, sleep=clock.sleep)
        limiter.wait(max_rate=0)

        clock.now = 1.0

        self.assertEqual(limiter.rate, 0)

    def test_concurrent_waiters_cannot_overbook_one_slot(self):
        clock = ControlledClock()
        sleeper = ControlledSleeper()
        limiter = RequestRateLimiter(clock=clock, sleep=sleeper)
        limiter.wait(max_rate=1)
        completed = []
        completed_lock = threading.Lock()
        first_completed = threading.Event()

        def wait_for_slot() -> None:
            limiter.wait(max_rate=1)
            with completed_lock:
                completed.append(clock())
                if len(completed) == 1:
                    first_completed.set()

        threads = [threading.Thread(target=wait_for_slot) for _ in range(2)]
        for thread in threads:
            thread.start()

        self.assertTrue(sleeper.first_waiters_ready.wait(timeout=1))
        self.assertEqual(limiter.rate, 1)

        clock.set(1.0)
        sleeper.release_first_waiters.set()
        self.assertTrue(sleeper.second_waiter_ready.wait(timeout=1))
        self.assertTrue(first_completed.wait(timeout=1))
        with completed_lock:
            self.assertEqual(completed, [1.0])

        clock.set(2.0)
        sleeper.release_second_waiter.set()
        for thread in threads:
            thread.join(timeout=1)
            self.assertFalse(thread.is_alive())

        with completed_lock:
            self.assertEqual(completed, [1.0, 2.0])


class TestAsyncRequestRateLimiter(IsolatedAsyncioTestCase):
    async def test_async_wait_uses_the_same_rolling_window(self):
        clock = FakeClock()
        limiter = RequestRateLimiter(
            clock=clock,
            async_sleep=clock.sleep_async,
        )

        await limiter.wait_async(max_rate=2)
        await limiter.wait_async(max_rate=2)
        await limiter.wait_async(max_rate=2)

        self.assertAlmostEqual(clock.now, 1.0)
        self.assertEqual(limiter.rate, 1)
