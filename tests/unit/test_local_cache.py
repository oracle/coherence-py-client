# Copyright (c) 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

import asyncio
import time
from typing import Any, Callable, Coroutine, Optional

import pytest

from coherence.local_cache import CacheStats, LocalCache, LocalEntry, NearCacheOptions
from coherence.util import cur_time_millis, millis_format_date


def test_local_entry() -> None:
    start: int = cur_time_millis()
    entry: LocalEntry[str, str] = LocalEntry("a", "b", 750)

    # check initial state after creation
    assert entry.key == "a"
    assert entry.value == "b"
    assert entry.ttl == 750
    assert entry.last_access >= start
    assert entry.bytes > 0

    # touch the entry and ensure the last_access has increased
    # over the insert time
    last: int = entry.last_access
    time.sleep(0.3)
    entry.touch()
    assert entry.last_access > last


def test_local_entry_str() -> None:
    entry: LocalEntry[str, str] = LocalEntry("a", "b", 500)

    result: str = str(entry)
    assert result == (
        f"LocalEntry(key=a, value=b," f" ttl=500ms," f" last-access={millis_format_date(entry.last_access)})"
    )

    time.sleep(0.6)

    result = str(entry)
    assert result == (
        f"LocalEntry(key=a, value=b," f" ttl=500ms," f" last-access={millis_format_date(entry.last_access)})"
    )


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
    assert stats.hit_rate == 0.083
    assert stats.size == 2

    # remove a value from the cache
    # ensure the returned value is what was associated
    # with the key.  Ensure the bytes has decreased
    # back to the snapshot taken earlier
    result = await cache.remove("b")
    assert result == "d"
    assert stats.bytes == stats_bytes


@pytest.mark.asyncio
async def test_get_all() -> None:
    cache: LocalCache[str, str] = LocalCache("test", NearCacheOptions(high_units=100))
    stats: CacheStats = cache.stats

    for i in range(10):
        key_value: str = str(i)
        await cache.put(key_value, key_value)

    assert stats.puts == 10

    results: dict[str, str] = await cache.get_all({"1", "2", "3", "4", "5"})
    assert len(results) == 5
    for i in range(1, 5):
        key_value = str(i)
        assert results[key_value] == key_value
    assert stats.gets == 5
    assert stats.hits == 5
    assert stats.misses == 0

    results = await cache.get_all({"8", "9", "10", "11"})
    assert len(results) == 2
    for i in range(8, 10):
        key_value = str(i)
        assert results[key_value] == key_value
    assert ("10" in results) is False
    assert ("11" in results) is False
    assert stats.gets == 9
    assert stats.hits == 7
    assert stats.misses == 2


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

    await asyncio.sleep(1.3)

    for i in range(5):
        assert await cache.get(str(i)) is None

    for i in range(5, 10):
        assert await cache.get(str(i)) == str(i)

    duration: int = stats.expires_duration
    assert stats.expires == 1
    assert stats.num_expired == 5
    assert duration > 0

    await asyncio.sleep(1.05)

    for i in range(10):
        assert await cache.get(str(i)) is None

    # assert correct expires count and
    # the duration has increased
    assert stats.expires == 2
    assert stats.num_expired == 10
    assert stats.expires_duration > duration


@pytest.mark.asyncio
async def test_pruning_units() -> None:
    options: NearCacheOptions = NearCacheOptions(high_units=100)
    cache: LocalCache[str, str] = LocalCache("test", options)
    stats: CacheStats = cache.stats

    for i in range(210):
        key_value: str = str(i)
        await cache.put(key_value, key_value, 0)

    cur_size: int = await cache.size()
    assert cur_size < 100
    assert stats.prunes == 6
    assert stats.prunes_duration > 0

    # assert that the oldest entries were pruned first
    for i in range(210 - cur_size, 210):
        key_value = str(i)
        assert await cache.get(key_value) == key_value


@pytest.mark.asyncio
async def test_pruning_memory() -> None:
    upper_bound_mem: int = 110 * 1024  # 110KB
    options: NearCacheOptions = NearCacheOptions(high_units_memory=upper_bound_mem)
    cache: LocalCache[str, str] = LocalCache("test", options)
    stats: CacheStats = cache.stats

    for i in range(210):
        key_value: str = str(i)
        await cache.put(key_value, key_value, 0)

    assert stats.prunes > 0
    assert stats.prunes_duration > 0
    assert stats.bytes < upper_bound_mem

    # assert that the oldest entries were pruned first
    for i in range(210 - await cache.size(), 210):
        key_value = str(i)
        assert await cache.get(key_value) == key_value


@pytest.mark.asyncio
async def test_stats_reset() -> None:
    upper_bound_mem: int = 110 * 1024  # 110KB
    options: NearCacheOptions = NearCacheOptions(ttl=500, high_units_memory=upper_bound_mem)
    cache: LocalCache[str, str] = LocalCache("test", options)
    stats: CacheStats = cache.stats

    for i in range(210):
        key_value: str = str(i)
        await cache.put(key_value, key_value)
        await cache.get(key_value)

    await cache.get("none")
    await cache.put("A", "B", 0)

    print(f"### DEBUG {time.time_ns() // 1_000_000}")
    print(f"### DEBUG {stats}")
    print(f"### DEBUG {cache._expiries}")

    await asyncio.sleep(2.0)

    print(f"### DEBUG {time.time_ns() // 1_000_000}")
    print(f"### DEBUG2 {stats}")
    print(f"### DEBUG2 {cache._expiries}")

    assert await cache.size()

    print(f"### DEBUG3 {stats}")
    print(f"### DEBUG3 {cache._expiries}")

    assert await cache.size() == 1

    print(f"### DEBUG4 {stats}")
    print(f"### DEBUG4 {cache._expiries}")

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


@pytest.mark.asyncio
async def test_clear() -> None:
    async def do_clear(cache: LocalCache) -> None:
        await cache.clear()

    await _validate_clear_reset(do_clear)


@pytest.mark.asyncio
async def test_release() -> None:
    async def do_release(cache: LocalCache) -> None:
        await cache.release()

    await _validate_clear_reset(do_release)


@pytest.mark.asyncio
async def test_local_cache_str() -> None:
    options: NearCacheOptions = NearCacheOptions(high_units=300)
    cache: LocalCache[str, str] = LocalCache("test", options)

    for i in range(210):
        key_value: str = str(i)
        await cache.put(key_value, key_value, 500)
        await cache.get(key_value)

    await cache.get("none")
    await cache.put("A", "B", 0)

    result: str = str(cache)
    stats: str = (
        f"CacheStats(puts=211, gets=211, hits=210, misses=1,"
        f" misses-duration=0ms, hit-rate=0.995, prunes=0, num-pruned=0, prunes-duration=0ms,"
        f" size=211, expires=0, num-expired=0, expires-duration=0ms, memory-bytes={cache.stats.bytes})"
    )

    assert result == f"LocalCache(name=test, options={str(options)}" f", stats={stats})"


async def _validate_clear_reset(reset: Callable[[LocalCache], Coroutine[Any, Any, None]]) -> None:
    options: NearCacheOptions = NearCacheOptions(high_units=300)
    cache: LocalCache[str, str] = LocalCache("test", options)
    stats: CacheStats = cache.stats

    for i in range(210):
        key_value: str = str(i)
        await cache.put(key_value, key_value)
        await cache.get(key_value)

    assert stats.size == 210
    assert stats.bytes > 1000

    # store current states to clear impacts the appropriate stats
    puts: int = stats.puts
    gets: int = stats.gets
    misses: int = stats.misses
    misses_duration: int = stats.misses_duration
    prunes: int = stats.prunes
    prunes_duration: int = stats.prunes_duration
    expires: int = stats.expires
    expires_duration: int = stats.expires_duration
    hit_rate: float = stats.hit_rate

    await reset(cache)

    assert stats.puts == puts
    assert stats.gets == gets
    assert stats.misses == misses
    assert stats.misses_duration == misses_duration
    assert stats.prunes == prunes
    assert stats.prunes_duration == prunes_duration
    assert stats.expires == expires
    assert stats.expires_duration == expires_duration
    assert stats.hit_rate == hit_rate
    assert stats.size == 0
    assert stats.bytes == 0
