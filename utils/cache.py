import asyncio
from collections import OrderedDict
from time import time
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class AsyncSnapshotCache(Generic[T]):
    def __init__(self, ttl: int = 300, max_size: int = 1000) -> None:
        self.ttl = ttl
        self.max_size = max_size
        self._cache: OrderedDict[str, tuple[T, float]] = OrderedDict()
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> T | None:
        async with self._lock:
            if key not in self._cache:
                return None

            value, timestamp = self._cache[key]
            if time() - timestamp > self.ttl:
                del self._cache[key]
                return None

            self._cache.move_to_end(key)
            return value

    async def set(self, key: str, value: T) -> None:
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
            elif len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)

            self._cache[key] = (value, time())

    async def delete(self, key: str) -> None:
        async with self._lock:
            if key in self._cache:
                del self._cache[key]

    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()

    async def size(self) -> int:
        async with self._lock:
            return len(self._cache)


_cache_instance: AsyncSnapshotCache[Any] | None = None


def get_cache(ttl: int = 300, max_size: int = 1000) -> AsyncSnapshotCache[Any]:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = AsyncSnapshotCache(ttl=ttl, max_size=max_size)
    return _cache_instance
