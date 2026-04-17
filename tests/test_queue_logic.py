import asyncio
import time
import unittest


class TokenBucket:
    def __init__(self, rate, capacity):
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


class TestQueueLogic(unittest.IsolatedAsyncioTestCase):
    async def test_worker_processing_order(self):
        queue = asyncio.Queue()
        limiter = TokenBucket(rate=100, capacity=10)
        results = []

        async def mock_perform_forward(task_id):
            await asyncio.sleep(0.01)
            results.append(task_id)
            return True

        async def worker():
            while True:
                task = await queue.get()
                await limiter.wait_for_token()
                await mock_perform_forward(task["id"])
                queue.task_done()

        worker_task = asyncio.create_task(worker())

        for i in range(5):
            await queue.put({"id": i})

        await queue.join()
        worker_task.cancel()

        self.assertEqual(results, [0, 1, 2, 3, 4])

    async def test_rate_limiting_delay(self):
        limiter = TokenBucket(rate=2, capacity=1)

        start = time.monotonic()
        await limiter.wait_for_token()
        await limiter.wait_for_token()
        duration = time.monotonic() - start

        self.assertGreaterEqual(duration, 0.45)


if __name__ == "__main__":
    unittest.main()
