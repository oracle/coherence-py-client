# Copyright (c) 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

import asyncio
import time
from datetime import datetime, timezone
from typing import Generic, Optional, Tuple, TypeVar

from pympler import asizeof

from . import MapEntry
from .client import NearCacheOptions

K = TypeVar("K")
V = TypeVar("V")


class LocalEntry(MapEntry[K, V]):

    def __init__(self, key: K, value: V, ttl: int):
        super().__init__(key, value)
        self._ttl_orig: int = ttl
        self._ttl: int = ttl * 1_000_000
        self._insert_time = time.time_ns()
        self._last_access = self._insert_time
        self._size = asizeof.asizeof(self)

    @property
    def bytes(self) -> int:
        return self._size

    @property
    def ttl(self) -> int:
        return self._ttl_orig

    @property
    def insert_time(self) -> int:
        return self._insert_time

    @property
    def last_access(self) -> int:
        return self._last_access

    def touch(self) -> None:
        self._last_access = time.time_ns()

    def expired(self, now: int) -> bool:
        return 0 < self._ttl < now - self._insert_time

    def _nanos_format_date(self, nanos: int) -> str:
        dt = datetime.fromtimestamp(nanos / 1e9, timezone.utc)
        return "{}{:03.0f}".format(dt.strftime("%Y-%m-%dT%H:%M:%S.%f"), nanos % 1e3)

    def __str__(self) -> str:
        return (
            f"LocalEntry(key={self._key}, value={self._value},"
            f" ttl={self._ttl // 1_000_000}ms, insert-time={self._nanos_format_date(self._insert_time)}"
            f" last-access={self._nanos_format_date(self._last_access)},"
            f" expired={self.expired(time.time_ns())})"
        )


class CacheStats:

    def __init__(self, local_cache: "LocalCache[K, V]"):
        self._local_cache: "LocalCache[K, V]" = local_cache
        self._hits: int = 0
        self._misses: int = 0
        self._puts: int = 0
        self._gets: int = 0
        self._memory: int = 0
        self._prunes: int = 0
        self._expires: int = 0
        self._expires_nanos: int = 0
        self._prunes_nanos: int = 0
        self._misses_nanos: int = 0

    @property
    def hits(self) -> int:
        return self._hits

    @property
    def misses(self) -> int:
        return self._misses

    @property
    def misses_duration(self) -> int:
        return self._misses_nanos

    @property
    def hit_rate(self) -> float:
        hits: int = self.hits
        misses: int = self.misses
        total = hits + misses

        return 0.0 if total == 0 else round((float(hits) / float(misses)), 2)

    @property
    def puts(self) -> int:
        return self._puts

    @property
    def gets(self) -> int:
        return self.hits + self.misses

    @property
    def prunes(self) -> int:
        return self._prunes

    @property
    def expires(self) -> int:
        return self._expires

    @property
    def prunes_duration(self) -> int:
        return self._prunes_nanos

    @property
    def expires_duration(self) -> int:
        return self._expires_nanos

    @property
    def size(self) -> int:
        return len(self._local_cache.storage)

    @property
    def bytes(self) -> int:
        return self._memory

    def reset(self) -> None:
        self._prunes = 0
        self._prunes_nanos = 0
        self._misses = 0
        self._misses_nanos = 0
        self._hits = 0
        self._puts = 0
        self._expires = 0
        self._expires_nanos = 0

    def _register_hit(self) -> None:
        self._hits += 1

    def _register_miss(self) -> None:
        self._misses += 1

    def _register_put(self) -> None:
        self._puts += 1

    def _register_get(self) -> None:
        self._gets += 1

    def _update_memory(self, size: int) -> None:
        self._memory += size

    def _register_prune_nanos(self, nanos: int) -> None:
        self._prunes += 1
        self._prunes_nanos += nanos

    def _register_misses_nanos(self, nanos: int) -> None:
        self._misses_nanos += nanos

    def _register_expires(self, count: int, nanos: int) -> None:
        self._expires += count
        self._expires_nanos += nanos

    def __str__(self) -> str:
        return (
            f"CacheStats(puts={self._puts}, gets={self._gets}, hits={self._hits}"
            f", misses={self._misses}, misses-duration={self._misses_nanos}ns"
            f", hit-rate={self.hit_rate}, prunes={self._prunes}"
            f", prunes-duration={self._prunes_nanos}ns, size={self.size}"
            f", expires={self._expires}, expires-duration={self._expires_nanos}ns"
            f", memory-bytes={self._memory})"
        )


# noinspection PyProtectedMember
class LocalCache(Generic[K, V]):

    def __init__(self, name: str, options: NearCacheOptions):
        self._name: str = name
        self._options: NearCacheOptions = options
        self._stats: CacheStats = CacheStats(self)
        self._data: dict[K, Optional[LocalEntry[K, V]]] = dict()
        self._lock: asyncio.Lock = asyncio.Lock()

    async def put(self, key: K, value: V, ttl: Optional[int] = None) -> Optional[V]:
        async with self._lock:
            stats: CacheStats = self.stats
            storage: dict[K, Optional[LocalEntry[K, V]]] = self.storage
            stats._register_put()
            self._prune()

            old_entry: Optional[LocalEntry[K, V]] = storage.get(key, None)
            if old_entry is not None:
                stats._update_memory(-old_entry.bytes)

            entry: LocalEntry[K, V] = LocalEntry(key, value, ttl if ttl is not None else self.options.ttl)
            stats._update_memory(entry.bytes)

            storage[key] = entry

            return None if old_entry is None else old_entry.value

    async def get(self, key: K) -> Optional[V]:
        async with self._lock:
            storage: dict[K, Optional[LocalEntry[K, V]]] = self.storage
            stats: CacheStats = self.stats
            self._expire()

            entry: Optional[LocalEntry[K, V]] = storage.get(key, None)
            if entry is None:
                stats._register_miss()
                return None

            stats._register_hit()
            entry._last_access = time.time_ns()

            return entry.value

    async def get_all(self, keys: set[K]) -> dict[K, V]:
        async with self._lock:
            self._expire()

            stats: CacheStats = self.stats
            results: dict[K, V] = dict()

            for key in keys:
                entry: Optional[LocalEntry[K, V]] = self.storage.get(key, None)
                if entry is None:
                    stats._register_miss()
                    continue

                stats._register_hit()
                entry._last_access = time.time_ns()

                results[key] = entry.value

            return results

    async def remove(self, key: K) -> Optional[V]:
        async with self._lock:
            self._expire()

            entry: Optional[LocalEntry[K, V]] = self.storage.get(key, None)

            if entry is None:
                return None

            self.stats._update_memory(-entry.bytes)
            return entry.value

    async def size(self) -> int:
        async with self._lock:
            self._expire()

            return len(self.storage)

    async def clear(self) -> None:
        async with self._lock:
            self._data = dict()

            self.stats._memory = 0

    async def release(self) -> None:
        await self.clear()

    @property
    def stats(self) -> CacheStats:
        return self._stats

    @property
    def name(self) -> str:
        return self._name

    @property
    def storage(self) -> dict[K, Optional[LocalEntry[K, V]]]:
        return self._data

    @property
    def options(self) -> NearCacheOptions:
        return self._options

    def _prune(self) -> None:
        self._expire()

        storage: dict[K, Optional[LocalEntry[K, V]]] = self.storage
        options: NearCacheOptions = self.options
        prune_factor: float = options.prune_factor
        high_units: int = options.high_units
        high_units_used: bool = high_units > 0
        high_units_mem: int = options.high_unit_memory
        mem_units_used: bool = high_units_mem > 0
        cur_size = len(storage)
        start = time.time_ns()

        if (high_units_used and high_units < cur_size + 1) or (mem_units_used and high_units_mem < self.stats.bytes):
            stats: CacheStats = self.stats

            to_sort: list[Tuple[int, K]] = []
            for key, value in storage.items():
                to_sort.append((value.last_access, key))  # type: ignore

            sorted(to_sort, key=lambda x: x[0])

            target_size: int = int(round(float((cur_size if high_units_used else stats.bytes) * prune_factor)))

            for item in to_sort:
                entry: Optional[LocalEntry[K, V]] = storage.pop(item[1])
                stats._update_memory(-entry.bytes)  # type: ignore

                if (len(storage) if high_units_used else stats._memory) <= target_size:
                    break

            end = time.time_ns()
            stats._register_prune_nanos(end - start)

    def _expire(self) -> None:
        storage: dict[K, Optional[LocalEntry[K, V]]] = self.storage
        start = time.time_ns()
        keys: list[K] = [key for key, entry in storage.items() if entry.expired(start)]  # type: ignore
        stats: CacheStats = self.stats

        for key in keys:
            entry: Optional[LocalEntry[K, V]] = storage.pop(key)
            stats._update_memory(-entry.bytes)  # type: ignore

        size: int = len(keys)
        if size > 0:
            end = time.time_ns()
            stats._register_expires(size, end - start)

    def __str__(self) -> str:
        return f"LocalCache(name={self.name}, options={self.options}" f", stats={self.stats})"
