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
    """
    A MapEntry implementation that includes metadata
    to allow for expiry and pruning within a local
    cache.
    """

    def __init__(self, key: K, value: V, ttl: int):
        """
        Constructs a new LocalEntry.

        :param key: the entry key
        :param value: the entry value
        :param ttl: the time-to-live for this entry
        """
        super().__init__(key, value)
        self._ttl_orig: int = ttl
        self._ttl: int = ttl * 1_000_000
        self._insert_time = time.time_ns()
        self._last_access = self._insert_time
        self._size = asizeof.asizeof(self)

    @property
    def bytes(self) -> int:
        """
        :return: the size in bytes of this entry
        """
        return self._size

    @property
    def ttl(self) -> int:
        """
        :return: the time-to-live of this entry
        """
        return self._ttl_orig

    @property
    def insert_time(self) -> int:
        """
        :return: the insert time, in nanos, of this entry
        """
        return self._insert_time

    @property
    def last_access(self) -> int:
        """
        :return: the last time, in nanos, this entry was accessed
        """
        return self._last_access

    def touch(self) -> None:
        """
        Updates the last accessed time of this entry.
        """
        self._last_access = time.time_ns()

    def expired(self, now: int) -> bool:
        """
        Determines if this entry is expired relative to the given
        time (in nanos).

        :param now:  the time to compare against (in nanos)
        :return: True if expired, otherwise False
        """
        return 0 < self._ttl < now - self._insert_time

    def _nanos_format_date(self, nanos: int) -> str:
        """
        Format the given time in nanos to a readable format.

        :param nanos: the nano time to format
        :return: the formatted date
        """
        dt = datetime.fromtimestamp(nanos / 1e9, timezone.utc)
        return "{}{:03.0f}".format(dt.strftime("%Y-%m-%dT%H:%M:%S.%f"), nanos % 1e3)

    def __str__(self) -> str:
        return (
            f"LocalEntry(key={self.key}, value={self.value},"
            f" ttl={self.ttl}ms, insert-time={self._nanos_format_date(self.insert_time)}"
            f" last-access={self._nanos_format_date(self.last_access)},"
            f" expired={self.expired(time.time_ns())})"
        )


class CacheStats:
    """
    Tracking statistics for LocalCaches.
    """

    def __init__(self, local_cache: "LocalCache[K, V]"):
        """
        Constructs a new CacheStats.

        :param local_cache: the associated LocalCache
        """
        self._local_cache: "LocalCache[K, V]" = local_cache
        self._hits: int = 0
        self._misses: int = 0
        self._puts: int = 0
        self._memory: int = 0
        self._prunes: int = 0
        self._expires: int = 0
        self._expires_nanos: int = 0
        self._prunes_nanos: int = 0
        self._misses_nanos: int = 0

    @property
    def hits(self) -> int:
        """
        :return: the number of cache hits
        """
        return self._hits

    @property
    def misses(self) -> int:
        """
        :return: the number of cache misses
        """
        return self._misses

    @property
    def misses_duration(self) -> int:
        """
        :return: the accumulated total of nanos spent when a cache
                 miss occurs and a remote get is made
        """
        return self._misses_nanos

    @property
    def hit_rate(self) -> float:
        """
        :return: the ratio of hits to misses
        """
        hits: int = self.hits
        misses: int = self.misses
        total = hits + misses

        return 0.0 if total == 0 else round((float(hits) / float(misses)), 2)

    @property
    def puts(self) -> int:
        """
        :return: the total number of puts
        """
        return self._puts

    @property
    def gets(self) -> int:
        """
        :return: the total number of gets
        """
        return self.hits + self.misses

    @property
    def prunes(self) -> int:
        """
        :return: the number of times the cache was pruned due to exceeding
                 configured limits
        """
        return self._prunes

    @property
    def expires(self) -> int:
        """
        :return: the number of entries that have been expired
        """
        return self._expires

    @property
    def prunes_duration(self) -> int:
        """
        :return: the accumulated total of nanos spent when a cache
                 prune occurs
        """
        return self._prunes_nanos

    @property
    def expires_duration(self) -> int:
        """
        :return: the accumulated total of nanos spent when cache expiry
                 occurs
        """
        return self._expires_nanos

    @property
    def size(self) -> int:
        """
        :return: the number of local cache entries
        """
        return len(self._local_cache.storage)

    @property
    def bytes(self) -> int:
        """
        :return: the total number of bytes the local cache is consuming
        """
        return self._memory

    def reset(self) -> None:
        """
        Resets all statistics aside from memory consumption and size.

        :return: None
        """
        self._prunes = 0
        self._prunes_nanos = 0
        self._misses = 0
        self._misses_nanos = 0
        self._hits = 0
        self._puts = 0
        self._expires = 0
        self._expires_nanos = 0

    def _register_hit(self) -> None:
        """
        Register a hit.

        :return: None
        """
        self._hits += 1

    def _register_miss(self) -> None:
        """
        Register a miss.

        :return: None
        """
        self._misses += 1

    def _register_put(self) -> None:
        """
        Register a put.

        :return: None
        """
        self._puts += 1

    def _update_memory(self, size: int) -> None:
        """
        Update the current memory total.

        :param size: the memory amount to increase/decrease
        :return: None
        """
        self._memory += size

    def _register_prune_nanos(self, nanos: int) -> None:
        """
        Register prune statistics.

        :param nanos: the nanos spent on a prune operation
        :return: None
        """
        self._prunes += 1
        self._prunes_nanos += nanos

    def _register_misses_nanos(self, nanos: int) -> None:
        """
        Register miss nanos.

        :param nanos: the nanos spent when a cache miss occurs
        :return: None
        """
        self._misses_nanos += nanos

    def _register_expires(self, count: int, nanos: int) -> None:
        """
        Register the number of entries expired and the nanos spent processing
        the expiry logic.

        :param count: the number of entries expired
        :param nanos: the time spent processing
        :return: None
        """
        self._expires += count
        self._expires_nanos += nanos

    def __str__(self) -> str:
        return (
            f"CacheStats(puts={self.puts}, gets={self.gets}, hits={self.hits}"
            f", misses={self.misses}, misses-duration={self.misses_duration}ns"
            f", hit-rate={self.hit_rate}, prunes={self.prunes}"
            f", prunes-duration={self.prunes_duration}ns, size={self.size}"
            f", expires={self.expires}, expires-duration={self.expires_duration}ns"
            f", memory-bytes={self.bytes})"
        )


# noinspection PyProtectedMember
class LocalCache(Generic[K, V]):
    """
    A local cache of entries.  This cache will expire entries as they ripen
    and will prune the cache down to any configured watermarks defined
    in the NearCacheOptions
    """

    def __init__(self, name: str, options: NearCacheOptions):
        """
        Constructs a new LocalCache.

        :param name: the name of the local cache
        :param options: the NearCacheOptions configuring this LocalCache
        """
        self._name: str = name
        self._options: NearCacheOptions = options
        self._stats: CacheStats = CacheStats(self)
        self._storage: dict[K, Optional[LocalEntry[K, V]]] = dict()
        self._lock: asyncio.Lock = asyncio.Lock()

    async def put(self, key: K, value: V, ttl: Optional[int] = None) -> Optional[V]:
        """
        Associates the specified value with the specified key in this cache. If the
        cache previously contained a mapping for this key, the old value is replaced.

        :param key: the key with which the specified value is to be associated
        :param value: the value to be associated with the specified key
        :param ttl: the time-to-live (in millis) of this entry
        :return: the previous value associated with the specified key, or `None`
         if there was no mapping for key. A `None` return can also indicate
         that the map previously associated `None` with the specified key
         if the implementation supports `None` values
        """
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
        """
        Returns the value to which this cache maps the specified key.

        :param key: the key whose associated value is to be returned
        """
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
        """
        Get all the specified keys if they are in the cache. For each key that is in the cache,
        that key and its corresponding value will be placed in the cache that is returned by
        this method. The absence of a key in the returned map indicates that it was not in the cache,
        which may imply (for caches that can load behind the scenes) that the requested data
        could not be loaded.

        :param keys: an Iterable of keys that may be in this cache
        :return: a dict containing the keys/values that were found in the
         local cache
        """
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
        """
        Removes the mapping for a key from this cache if it is present.

        :param key: key whose mapping is to be removed from the cache
        :return: the previous value associated with key, or `None` if there was no mapping for key
        """
        async with self._lock:
            self._expire()

            entry: Optional[LocalEntry[K, V]] = self.storage.get(key, None)

            if entry is None:
                return None

            self.stats._update_memory(-entry.bytes)
            return entry.value

    async def size(self) -> int:
        """
        Signifies the number of key-value mappings in this cache.

        :return: the number of key-value mappings in this cache
        """
        async with self._lock:
            self._expire()

            return len(self.storage)

    async def clear(self) -> None:
        """
        Clears all the mappings in the cache.
        """
        async with self._lock:
            self._storage = dict()

            self.stats._memory = 0

    async def release(self) -> None:
        """
        Release local resources associated with instance.
        """
        await self.clear()

    @property
    def stats(self) -> CacheStats:
        """
        :return: the statistics for this cache
        """
        return self._stats

    @property
    def name(self) -> str:
        """
        :return: the name of this cache
        """
        return self._name

    @property
    def storage(self) -> dict[K, Optional[LocalEntry[K, V]]]:
        """
        :return: the local storage for this cache
        """
        return self._storage

    @property
    def options(self) -> NearCacheOptions:
        """
        :return: the NearCacheOptions for this cache
        """
        return self._options

    def _prune(self) -> None:
        """
        Prunes this cache based on NearCacheOptions configuration.

        :return: None
        """
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
        """
        Process and remove any expired entries from the cache.

        :return: None
        """
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
