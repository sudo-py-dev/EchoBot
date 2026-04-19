import asyncio
import time


class RateLimiter:
    def __init__(self, rate: float, capacity: float):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def wait_for_token(self):
        async with self._lock:
            while True:
                now = time.monotonic()
                delta = now - self.last_update
                self.tokens = min(self.capacity, self.tokens + delta * self.rate)
                self.last_update = now

                if self.tokens >= 1:
                    self.tokens -= 1
                    return

                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)


global_limiter = RateLimiter(rate=25, capacity=30)
