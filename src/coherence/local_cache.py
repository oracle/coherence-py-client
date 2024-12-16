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
        self, ttl: Optional[int] = None, high_units: int = 0, high_units_memory: int = 0, prune_factor: float = 0.80
    ) -> None:
        """
        Constructs a new NearCacheOptions.  These options, when present, will configure
        a NamedMap or NamedCache with a \"near cache\".  This near cache will locally
        cache entries to reduce the need to go to the network for entries that are
        frequently accessed.  Changes made to, or removal of entries from the remote
        cache will be reflected in the near cache.

        :param ttl: the time-to-live, in millis, for entries held in the near cache.
         Expiration resolution is to the 1/4 second, thus the minimum positive
         ttl value is 250.  If the ttl is zero, then no expiry will be applied
        :param high_units: the maximum number of entries to be held by
         the near cache.  If this value is exceeded, the cache will be pruned
         down by the percentage defined by the prune_factor parameter
        :param high_units_memory: the maximum number of entries, in bytes,
         that may be held by the near cache.  If this value is exceeded, the
         cache will be pruned down by the percentage defined by the
         prune_factor parameter
        :param prune_factor: the prune factor defines the target cache
         size after exceeding the high_units or high_units_memory
         high-water mark
        """
        super().__init__()
        if high_units < 0 or high_units_memory < 0:
            raise ValueError("values for high_units and high_units_memory must be positive")
        if ttl is None and high_units == 0 and high_units_memory == 0:
            raise ValueError("at least one option must be specified")
        if ttl is not None and ttl < 0:
            raise ValueError("ttl cannot be less than zero")
        if ttl is not None and 0 < ttl < 250:
            raise ValueError("ttl has 1/4 second resolution;  minimum TTL is 250")
        if high_units != 0 and high_units_memory != 0:
            raise ValueError("high_units and high_units_memory cannot be used together; specify one or the other")
        if prune_factor < 0.1 or prune_factor > 1:
            raise ValueError("prune_factor must be between .1 and 1")

        self._ttl = ttl if ttl is not None and ttl >= 0 else 0
        self._high_units = high_units
        self._high_units_memory = high_units_memory
        self._prune_factor = prune_factor

    def __str__(self) -> str:
        """
        Returns a string representation of this NearCacheOptions instance.

        :return: string representation of this NearCacheOptions instance
        """
        return (
            f"NearCacheOptions(ttl={self.ttl}ms, high-units={self.high_units}"
            f", high-units-memory={self.high_unit_memory}"
            f", prune-factor={self.prune_factor:.2f})"
        )

    def __eq__(self, other: Any) -> bool:
        """
        Compare two NearCacheOptions for equality.

        :param other: the NearCacheOptions to compare against
        :return: True if equal otherwise False
        """
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
        """
        The time-to-live to be applied to entries inserted into the
        near cache.

        :return: the ttl to be applied to entries inserted into the
         near cache
        """
        return self._ttl

    @property
    def high_units(self) -> int:
        """
        The maximum number of entries that may be held by the near cache.
        If this value is exceeded, the cache will be pruned down by the
        percentage defined by the prune_factor.

        :return: the maximum number of entries that may be held by the
         near cache
        """
        return self._high_units

    @property
    def high_unit_memory(self) -> int:
        """
        The maximum number of entries, in bytes, that may be held in the near cache.
        If this value is exceeded, the cache will be pruned down by the
        percentage defined by the prune_factor.

        :return: the maximum number of entries, in bytes, that may be held
         by the near cache
        """
        return self._high_units_memory

    @property
    def prune_factor(self) -> float:
        """
        This is percentage of units that will remain after a cache has
        been pruned.  When high_units is configured, this will be the number
        of entries.  When high_units_memory is configured, this will be the
        size, in bytes, of the cache will be pruned down to.

        :return: the target cache size after pruning occurs
        """
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
        self._size += asizeof.asizeof(self._size)

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

    def __str__(self) -> str:
        return (
            f"LocalEntry(key={self.key}, value={self.value},"
            f" ttl={self.ttl}ms,"
            f" last-access={millis_format_date(self.last_access)})"
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
        self._pruned_count: int = 0
        self._expires: int = 0
        self._expired_count: int = 0
        self._expires_millis: int = 0
        self._prunes_millis: int = 0
        self._misses_millis: int = 0

    @property
    def hits(self) -> int:
        """
        The number of times an entry was found in the near cache.

        :return: the number of cache hits
        """
        return self._hits

    @property
    def misses(self) -> int:
        """
        The number of times an entry was not found in the near cache.

        :return: the number of cache misses
        """
        return self._misses

    @property
    def misses_duration(self) -> int:
        """
        The accumulated time, in millis, spent for a cache miss.

        :return: the accumulated total of millis spent when a cache
                 miss occurs and a remote get is made
        """
        return self._misses_millis

    @property
    def hit_rate(self) -> float:
        """
        The ration of hits to misses.

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
        The total number of puts that have been made against the near
        cache.

        :return: the total number of puts
        """
        return self._puts

    @property
    def gets(self) -> int:
        """
        The total number of gets that have been made against the near
        cache.

        :return: the total number of gets
        """
        return self.hits + self.misses

    @property
    def prunes(self) -> int:
        """
        :return: the number of times the cache was pruned due to exceeding
                 the configured high-water mark
        """
        return self._prunes

    @property
    def expires(self) -> int:
        """
        The number of times expiry of entries has been processed.

        :return: the number of times expiry was processed
        """
        return self._expires

    @property
    def num_pruned(self) -> int:
        """
        The total number of entries that have been removed due to
        exceeding the configured high-water mark.

        :return: the number of entries pruned
        """
        return self._pruned_count

    @property
    def num_expired(self) -> int:
        """
        The total number of entries that have been removed due to
        expiration.

        :return: the number of entries that was expired
        """
        return self._expired_count

    @property
    def prunes_duration(self) -> int:
        """
        The accumulated total time, in millis, spent pruning the
        near cache

        :return: the accumulated total of millis spent pruning the near
         cache
        """
        return self._prunes_millis

    @property
    def expires_duration(self) -> int:
        """
        The accumulated total time, in millis, spent processing expiration
        of entries in the near cache

        :return: the accumulated total of millis spent expiring entries
         in the near cache
        """
        return self._expires_millis

    @property
    def size(self) -> int:
        """
        The total number of entries held by the near cache.

        :return: the number of local cache entries
        """
        return len(self._local_cache.storage)

    @property
    def bytes(self) -> int:
        """
        The total number of bytes the entries of the near cache is
        consuming.

        :return: The total number of bytes the entries of the near cache is
         consuming
        """
        return self._memory

    def reset(self) -> None:
        """
        Resets all statistics aside from memory consumption and size.

        :return: None
        """
        self._prunes = 0
        self._prunes_millis = 0
        self._pruned_count = 0
        self._misses = 0
        self._misses_millis = 0
        self._hits = 0
        self._puts = 0
        self._expires = 0
        self._expires_millis = 0
        self._expired_count = 0

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
        self._prunes += 1
        self._pruned_count += count
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
        self._expires += 1
        self._expired_count += count
        self._expires_millis += millis if millis > 0 else 1

    def __str__(self) -> str:
        """
        :return: the string representation of this CacheStats instance.
        """
        return (
            f"CacheStats(puts={self.puts}, gets={self.gets}, hits={self.hits}"
            f", misses={self.misses}, misses-duration={self.misses_duration}ms"
            f", hit-rate={self.hit_rate}, prunes={self.prunes}, num-pruned={self.num_pruned}"
            f", prunes-duration={self.prunes_duration}ms, size={self.size}"
            f", expires={self.num_expired}, num-expired={self.expires}"
            f", expires-duration={self.expires_duration}ms"
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
            entry: Optional[LocalEntry[K, V]] = self.storage.pop(key, None)

            if entry is None:
                return None

            self._remove_expiry(entry)
            self.stats._update_memory(-entry.bytes)
            return entry.value

    async def contains_key(self, key: K) -> bool:
        """
        Returns `true` if the specified key is mapped a value within the cache.

        :param key: the key whose presence in this cache is to be tested
        :return: resolving to `true` if the key is mapped to a value, or `false` if it does not
        """
        return key in self._storage

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
            self._expiries = OrderedDict()

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
                if value is not None:
                    to_sort.append((value.last_access, key))

            to_sort = sorted(to_sort, key=lambda x: x[0])

            target_size: int = int(round(float((cur_size if high_units_used else stats.bytes) * prune_factor)))

            for item in to_sort:
                entry: Optional[LocalEntry[K, V]] = storage.pop(item[1])
                if entry is not None:
                    self._remove_expiry(entry)
                    stats._update_memory(-entry.bytes)
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
            print(f"### DEBUG PROCESSING BUCKET {expire_time}, current={now}")
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
                print(f"### DEBUG REMOVING BUCKET {bucket}, current={now}")
                expires.pop(bucket, None)

        end = cur_time_millis()
        if expired_count > 0:
            stats._register_expires(expired_count, end - now)

        # expiries have 1/4 second resolution, so only check
        # expiry in the same interval
        self._next_expiry = end + 250

    def _register_expiry(self, entry: LocalEntry[K, V]) -> None:
        """
        Register the expiry, if any, of provided entry.

        :param entry: the entry to register
        :return: None
        """
        if entry.ttl > 0:
            expires_at = entry.expires_at
            expires_map: dict[int, set[K]] = self._expiries
            if expires_at in expires_map:
                keys: set[K] = expires_map[expires_at]
                keys.add(entry.key)
            else:
                expires_map[expires_at] = {entry.key}

    def _remove_expiry(self, entry: LocalEntry[K, V]) -> None:
        """
        Removes the provided entry from expiry tracking.

        :param entry: the entry to register
        :return: None
        """
        if entry.ttl > 0:
            expires_at = entry.expires_at
            expires_map: dict[int, set[K]] = self._expiries
            if expires_at in expires_map:
                keys: set[K] = expires_map[expires_at]
                expire_key: K = entry.key
                if expire_key in keys:
                    keys.remove(expire_key)

    def __str__(self) -> str:
        """
        :return: the string representation of this LocalCache.
        """
        return f"LocalCache(name={self.name}, options={self.options}, stats={self.stats})"
