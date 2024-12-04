# Copyright (c) 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

import time
from typing import Optional

import pytest

from coherence.client import NearCacheOptions
from coherence.local_cache import CacheStats, LocalCache, LocalEntry


def test_local_entry() -> None:
    start: int = time.time_ns()
    entry: LocalEntry[str, str] = LocalEntry("a", "b", 100)

    # check initial state after creation
    assert entry.key == "a"
    assert entry.value == "b"
    assert entry.ttl == 100
    assert entry.insert_time > start
    assert entry.last_access == entry.insert_time
    assert entry.bytes > 0

    # touch the entry and ensure the last_access has increased
    # over the insert time
    entry.touch()
    assert entry.last_access > entry.insert_time

    # ensure the entry hasn't expired, then wait
    # for a period of time beyond the expiry time
    # and ensure it has expired
    assert entry.expired(time.time_ns()) is False
    time.sleep(0.2)
    assert entry.expired(time.time_ns()) is True


@pytest.mark.asyncio
async def test_basic_put_get_remove() -> None:
    options: NearCacheOptions = NearCacheOptions(high_units=10)
    cache: LocalCache[str, str] = LocalCache("test", options)
    result: Optional[str] = await cache.get("a")

    assert result is None

    stats: CacheStats = cache.stats

    # validate stats with a get against an empty cache
    assert stats.misses == 1
    assert stats.gets == 1
    assert stats.bytes == 0

    # check stats after a single put
    result = await cache.put("a", "b")
    assert result is None
    assert stats.puts == 1
    assert stats.gets == 1

    # check stats after a get for the value previously inserted
    result = await cache.get("a")
    assert result == "b"
    assert stats.misses == 1
    assert stats.gets == 2
    assert stats.bytes > 0

    # update the value
    result = await cache.put("a", "c")

    # snapshot the current size for validation later
    stats_bytes: int = stats.bytes

    # ensure previous value returned after update and stats
    # are accurate
    assert result == "b"
    assert stats.puts == 2
    assert stats.misses == 1
    assert stats.gets == 2

    # insert new value and validate stats
    result = await cache.put("b", "d")
    assert result is None
    assert stats.puts == 3
    assert stats.misses == 1
    assert stats.gets == 2
    assert stats.bytes > stats_bytes

    # issue a series of gets for a non-existent key
    for _ in range(10):
        await cache.get("c")

    # validate the stats including the hit-rate
    assert stats.gets == 12
    assert stats.hits == 1
    assert stats.misses == 11
    assert stats.hit_rate == 0.09
    assert stats.size == 2

    # remove a value from the cache
    # ensure the returned value is what was associated
    # with the key.  Ensure the bytes has decreased
    # back to the snapshot taken earlier
    result = await cache.remove("b")
    assert result == "d"
    assert stats.bytes == stats_bytes


@pytest.mark.asyncio
async def test_expiry() -> None:
    options: NearCacheOptions = NearCacheOptions(high_units=1000)
    cache: LocalCache[str, str] = LocalCache("test", options)
    stats: CacheStats = cache.stats

    for i in range(5):
        await cache.put(str(i), str(i), 1000)

    for i in range(5, 10):
        await cache.put(str(i), str(i), 2000)

    for i in range(10):
        await cache.get(str(i))

    assert await cache.size() == 10

    time.sleep(1.05)

    for i in range(5):
        assert await cache.get(str(i)) is None

    for i in range(5, 10):
        assert await cache.get(str(i)) == str(i)

    duration: int = stats.expires_duration
    assert stats.expires == 5
    assert duration > 0

    time.sleep(1.05)

    for i in range(10):
        assert await cache.get(str(i)) is None

    # assert correct expires count and
    # the duration has increased
    assert stats.expires == 10
    assert stats.expires_duration > duration


@pytest.mark.asyncio
async def test_pruning_units() -> None:
    options: NearCacheOptions = NearCacheOptions(high_units=100)
    cache: LocalCache[str, str] = LocalCache("test", options)
    stats: CacheStats = cache.stats

    for i in range(210):
        key_value: str = str(i)
        await cache.put(key_value, key_value, 0)

    # todo validate oldest entries pruned

    assert await cache.size() < 100
    assert stats.prunes == 6
    assert stats.prunes_duration > 0


@pytest.mark.asyncio
async def test_pruning_memory() -> None:
    upper_bound_mem: int = 110 * 1024  # 110KB
    options: NearCacheOptions = NearCacheOptions(high_units_memory=upper_bound_mem)
    cache: LocalCache[str, str] = LocalCache("test", options)
    stats: CacheStats = cache.stats

    for i in range(210):
        key_value: str = str(i)
        await cache.put(key_value, key_value, 0)

    # todo validate oldest entries pruned

    assert stats.prunes > 0
    assert stats.prunes_duration > 0

    assert stats.bytes < upper_bound_mem


@pytest.mark.asyncio
async def test_stats_reset() -> None:
    upper_bound_mem: int = 110 * 1024  # 110KB
    options: NearCacheOptions = NearCacheOptions(high_units_memory=upper_bound_mem)
    cache: LocalCache[str, str] = LocalCache("test", options)
    stats: CacheStats = cache.stats

    for i in range(210):
        key_value: str = str(i)
        await cache.put(key_value, key_value, 100)
        await cache.get(key_value)

    await cache.get("none")
    await cache.put("A", "B", 0)

    time.sleep(0.5)

    assert await cache.size() == 1

    print(str(stats))

    memory: int = stats.bytes
    assert stats.puts == 211
    assert stats.gets == 211
    assert stats.prunes > 0
    assert stats.prunes_duration > 0
    assert stats.expires > 0
    assert stats.expires_duration > 0
    assert stats.hits > 0
    assert stats.hit_rate > 0
    assert stats.misses > 0
    assert memory > 0

    stats.reset()

    assert stats.puts == 0
    assert stats.gets == 0
    assert stats.prunes == 0
    assert stats.prunes_duration == 0
    assert stats.expires == 0
    assert stats.expires_duration == 0
    assert stats.hits == 0
    assert stats.hit_rate == 0.0
    assert stats.misses == 0
    assert stats.bytes == memory
