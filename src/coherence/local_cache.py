# Copyright (c) 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.
from __future__ import annotations

import asyncio
from collections import OrderedDict
from typing import Any, Generic, Optional, Tuple, TypeVar

from pympler import asizeof

from .entry import MapEntry
from .util import cur_time_millis, millis_format_date

K = TypeVar("K")
V = TypeVar("V")


class NearCacheOptions:

    def __init__(
        self, ttl: int = 0, high_units: int = 0, high_units_memory: int = 0, prune_factor: float = 0.80
    ) -> None:
        super().__init__()
        if high_units < 0 or high_units_memory < 0:
            raise ValueError("values for high_units and high_units_memory must be positive")
        if ttl == 0 and high_units == 0 and high_units_memory == 0:
            raise ValueError("at least one option must be specified and non-zero")
        if ttl < 0:
            raise ValueError("ttl cannot be less than zero")
        if 0 < ttl < 250:
            raise ValueError("ttl has 1/4 second resolution;  minimum TTL is 250")
        if high_units != 0 and high_units_memory != 0:
            raise ValueError("high_units and high_units_memory cannot be used together; specify one or the other")
        if prune_factor < 0.1 or prune_factor > 1:
            raise ValueError("prune_factor must be between .1 and 1")

        self._ttl = ttl if ttl >= 0 else -1
        self._high_units = high_units
        self._high_units_memory = high_units_memory
        self._prune_factor = prune_factor

    def __str__(self) -> str:
        return (
            f"NearCacheOptions(ttl={self.ttl}ms, high-units={self.high_units}"
            f", high-units-memory={self.high_unit_memory}"
            f", prune-factor={self.prune_factor:.2f})"
        )

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True

        if isinstance(other, NearCacheOptions):
            return (
                self.ttl == other.ttl
                and self.high_units == other.high_units
                and self.high_unit_memory == other.high_unit_memory
                and self.prune_factor == other.prune_factor
            )

        return False

    @property
    def ttl(self) -> int:
        return self._ttl

    @property
    def high_units(self) -> int:
        return self._high_units

    @property
    def high_unit_memory(self) -> int:
        return self._high_units_memory

    @property
    def prune_factor(self) -> float:
        return self._prune_factor


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
        self._ttl: int = ttl
        now: int = cur_time_millis()
        # store when this entry expires (1/4 second resolution)
        self._expires: int = ((now + ttl) & ~0xFF) if ttl > 0 else 0
        self._last_access: int = now
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
        :return: the time-to-live , in millis, of this entry
        """
        return self._ttl

    @property
    def last_access(self) -> int:
        """
        :return: the last time, in millis, this entry was accessed
        """
        return self._last_access

    @property
    def expires_at(self) -> int:
        """
        :return: the time when this entry will expire
        """
        return self._expires

    def touch(self) -> None:
        """
        Updates the last accessed time of this entry.
        """
        self._last_access = cur_time_millis()

    def expired(self, now: int) -> bool:
        """
        Determines if this entry is expired relative to the given
        time (in millis).

        :param now:  the time to compare against (in millis)
        :return: True if expired, otherwise False
        """
        return now > 0 and now > self._expires

    def __str__(self) -> str:
        return (
            f"LocalEntry(key={self.key}, value={self.value},"
            f" ttl={self.ttl}ms,"
            f" last-access={millis_format_date(self.last_access)},"
            f" expired={self.expired(cur_time_millis())})"
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
        self._pruned: int = 0
        self._expires: int = 0
        self._expires_millis: int = 0
        self._prunes_millis: int = 0
        self._misses_millis: int = 0

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
    def num_pruned(self) -> int:
        """
        :return: the number of entries pruned
        """
        return self._pruned

    @property
    def misses_duration(self) -> int:
        """
        :return: the accumulated total of millis spent when a cache
                 miss occurs and a remote get is made
        """
        return self._misses_millis

    @property
    def hit_rate(self) -> float:
        """
        :return: the ratio of hits to misses
        """
        hits: int = self.hits
        misses: int = self.misses
        total = hits + misses

        if misses == 0 and hits > 0:
            return 1.0 if hits > 0 else 0.0

        return 0.0 if total == 0 else round((float(hits) / (float(total))), 3)

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
        :return: the accumulated total of millis spent when a cache
                 prune occurs
        """
        return self._prunes_millis

    @property
    def expires_duration(self) -> int:
        """
        :return: the accumulated total of millis spent when cache expiry
                 occurs
        """
        return self._expires_millis

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
        self._prunes_millis = 0
        self._misses = 0
        self._misses_millis = 0
        self._hits = 0
        self._puts = 0
        self._expires = 0
        self._expires_millis = 0

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

    def _register_prunes(self, count: int, millis: int) -> None:
        """
        Register prune statistics.

        :param count: the number of entries pruned
        :param millis: the number of millis spent on a prune operation
        :return: None
        """
        self._pruned += count
        self._prunes += 1
        self._prunes_millis += millis if millis > 0 else 1

    def _register_misses_millis(self, millis: int) -> None:
        """
        Register miss millis.

        :param millis: the millis spent when a cache miss occurs
        :return: None
        """
        self._misses_millis += millis

    def _register_expires(self, count: int, millis: int) -> None:
        """
        Register the number of entries expired and the millis spent processing
        the expiry logic.

        :param count: the number of entries expired
        :param millis: the time spent processing
        :return: None
        """
        self._expires += count
        self._expires_millis += millis if millis > 0 else 1

    def __str__(self) -> str:
        return (
            f"CacheStats(puts={self.puts}, gets={self.gets}, hits={self.hits}"
            f", misses={self.misses}, misses-duration={self.misses_duration}ms"
            f", hit-rate={self.hit_rate}, prunes={self.prunes}, num-pruned={self.num_pruned}"
            f", prunes-duration={self.prunes_duration}ms, size={self.size}"
            f", num-expired={self.expires}, expires-duration={self.expires_duration}ms"
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
        self._expiries: dict[int, set[K]] = OrderedDict()
        self._lock: asyncio.Lock = asyncio.Lock()
        self._next_expiry: int = 0

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
            self._register_expiry(entry)
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
            entry.touch()

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
                entry.touch()

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

        if (high_units_used and high_units < cur_size + 1) or (mem_units_used and high_units_mem < self.stats.bytes):
            start = cur_time_millis()
            stats: CacheStats = self.stats
            prune_count: int = 0

            to_sort: list[Tuple[int, K]] = []
            for key, value in storage.items():
                to_sort.append((value.last_access, key))  # type: ignore

            to_sort = sorted(to_sort, key=lambda x: x[0])

            target_size: int = int(round(float((cur_size if high_units_used else stats.bytes) * prune_factor)))

            for item in to_sort:
                entry: Optional[LocalEntry[K, V]] = storage.pop(item[1])
                stats._update_memory(-entry.bytes)  # type: ignore
                prune_count += 1

                if (len(storage) if high_units_used else stats._memory) <= target_size:
                    break

            end = cur_time_millis()
            stats._register_prunes(prune_count, end - start)

    def _expire(self) -> None:
        """
        Process and remove any expired entries from the cache.

        :return: None
        """
        expires: dict[int, set[K]] = self._expiries
        if len(expires) == 0:
            return

        now: int = cur_time_millis()
        if self._next_expiry > 0 and now < self._next_expiry:
            return

        storage: dict[K, Optional[LocalEntry[K, V]]] = self.storage
        stats: CacheStats = self.stats

        expired_count: int = 0
        exp_buckets_to_remove: list[int] = []

        for expire_time, keys in expires.items():
            if expire_time < now:
                exp_buckets_to_remove.append(expire_time)
                for key in keys:
                    entry: Optional[LocalEntry[K, V]] = storage.pop(key, None)
                    if entry is not None:
                        expired_count += 1
                        stats._update_memory(-entry.bytes)

            break

        if len(exp_buckets_to_remove) > 0:
            for bucket in exp_buckets_to_remove:
                expires.pop(bucket, None)

        if expired_count > 0:
            end = cur_time_millis()
            stats._register_expires(expired_count, end - now)

        # expiries have 1/4 second resolution, so only check
        # expiry in the same interval
        self._next_expiry = now + 256

    def _register_expiry(self, entry: LocalEntry[K, V]) -> None:
        if entry.ttl > 0:
            expires_at = entry.expires_at
            expires_map: dict[int, set[K]] = self._expiries

            if expires_at in expires_map:
                keys: set[K] = expires_map[expires_at]
                keys.add(entry.key)
            else:
                expires_map[expires_at] = {entry.key}

    def __str__(self) -> str:
        return f"LocalCache(name={self.name}, options={self.options}, stats={self.stats})"
