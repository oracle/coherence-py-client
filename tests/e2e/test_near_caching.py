# Copyright (c) 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

import asyncio
from typing import Optional

import pytest

from coherence import CacheOptions, CacheStats, Filters, NamedCache, NearCacheOptions, Processors, Session


@pytest.mark.asyncio
async def test_basic_put_get_remove(test_session: Session) -> None:
    cache: NamedCache[str, str] = await test_session.get_cache(
        "basic", CacheOptions(near_cache_options=NearCacheOptions(ttl=2000))
    )

    stats: Optional[CacheStats] = cache.near_cache_stats
    assert stats is not None

    result: Optional[str] = await cache.put("a", "b")
    assert result is None
    assert await cache.size() == 1
    assert stats.size == 0
    assert stats.puts == 0

    result = await cache.get("a")
    assert result == "b"
    assert stats.size == 1
    assert stats.puts == 1
    assert stats.gets == 1
    assert stats.hits == 0
    assert stats.misses == 1

    result = await cache.get("a")
    assert result == "b"
    assert stats.size == 1
    assert stats.puts == 1
    assert stats.gets == 2
    assert stats.hits == 1
    assert stats.misses == 1

    # allow entry to expire
    await asyncio.sleep(2.1)

    result = await cache.get("a")
    assert result == "b"
    assert stats.size == 1
    assert stats.puts == 2
    assert stats.gets == 3
    assert stats.hits == 1
    assert stats.misses == 2
    assert stats.expires == 1

    result = await cache.remove("a")
    assert result == "b"
    assert await cache.size() == 0
    assert stats.size == 0
    assert stats.puts == 2
    assert stats.gets == 3
    assert stats.hits == 1
    assert stats.misses == 2
    assert stats.expires == 1

    # re-populate the near cache
    await cache.put("a", "b")
    await cache.get("a")

    assert stats.size == 1
    assert stats.puts == 3
    assert stats.gets == 4
    assert stats.hits == 1
    assert stats.misses == 3
    assert stats.expires == 1

    # remove the entry via processor and ensure the near cache
    # is in the expected state
    await cache.invoke("a", Processors.conditional_remove(Filters.always()))
    await asyncio.sleep(1)

    assert stats.size == 0
    assert stats.puts == 3
    assert stats.gets == 4
    assert stats.hits == 1
    assert stats.misses == 3
    assert stats.expires == 1

    # re-populate the near cache
    # noinspection PyTypeChecker
    await cache.put("a", {"b": "d"})
    assert await cache.get("a") == {"b": "d"}

    assert stats.size == 1
    assert stats.puts == 4
    assert stats.gets == 5
    assert stats.hits == 1
    assert stats.misses == 4
    assert stats.expires == 1

    # update an entry via processor and ensure the near cache
    # is in the expected state
    await cache.invoke("a", Processors.update("b", "c"))
    assert await cache.get("a") == {"b": "c"}

    assert stats.size == 1
    assert stats.puts == 5
    assert stats.gets == 6
    assert stats.hits == 2
    assert stats.misses == 4
    assert stats.expires == 1


@pytest.mark.asyncio
async def test_get_all(test_session: Session) -> None:
    cache: NamedCache[str, str] = await test_session.get_cache(
        "basic", CacheOptions(near_cache_options=NearCacheOptions(ttl=2000))
    )

    stats: Optional[CacheStats] = cache.near_cache_stats
    assert stats is not None

    await cache.put_all({str(x): str(x) for x in range(10)})
    assert stats.size == 0
    assert stats.puts == 0
    assert stats.gets == 0
    assert stats.hits == 0
    assert stats.misses == 0

    result: dict[str, str] = {}
    count: int = 1
    async for entry in await cache.get_all({"0", "9"}):
        result[entry.key] = entry.value
        assert stats.size == count
        assert stats.puts == count
        assert stats.gets == 2
        assert stats.hits == 0
        assert stats.misses == 2
        count += 1

    assert result == {"0": "0", "9": "9"}

    # issue a get_all that has a mix of keys that are and are
    # not in the near cache
    result = {}
    async for entry in await cache.get_all({"0", "9", "1", "8"}):
        result[entry.key] = entry.value

    assert stats.size == 4
    assert stats.puts == 4
    assert stats.gets == 6
    assert stats.hits == 2
    assert stats.misses == 4

    assert result == {"0": "0", "9": "9", "1": "1", "8": "8"}

    # issue a get_all for only keys present in the near cache
    result = {}
    async for entry in await cache.get_all({"0", "9", "1", "8"}):
        result[entry.key] = entry.value

    assert stats.size == 4
    assert stats.puts == 4
    assert stats.gets == 10
    assert stats.hits == 6
    assert stats.misses == 4

    assert result == {"0": "0", "9": "9", "1": "1", "8": "8"}


@pytest.mark.asyncio
async def test_remove(test_session: Session) -> None:
    cache: NamedCache[str, str] = await test_session.get_cache(
        "basic", CacheOptions(near_cache_options=NearCacheOptions(ttl=2000))
    )

    stats: Optional[CacheStats] = cache.near_cache_stats
    assert stats is not None

    # populate the near cache
    await cache.put("a", "b")
    await cache.get("a")

    assert stats.size == 1
    assert stats.puts == 1
    assert stats.gets == 1
    assert stats.hits == 0
    assert stats.misses == 1
    assert stats.expires == 0

    # invalid mapping should have no impact on near cache
    await cache.remove_mapping("a", "c")

    assert stats.size == 1
    assert stats.puts == 1
    assert stats.gets == 1
    assert stats.hits == 0
    assert stats.misses == 1
    assert stats.expires == 0

    # assert near cache entry is removed
    await cache.remove_mapping("a", "b")

    assert stats.size == 0
    assert stats.puts == 1
    assert stats.gets == 1
    assert stats.hits == 0
    assert stats.misses == 1
    assert stats.expires == 0


@pytest.mark.asyncio
async def test_replace(test_session: Session) -> None:
    cache: NamedCache[str, str] = await test_session.get_cache(
        "basic", CacheOptions(near_cache_options=NearCacheOptions(ttl=2000))
    )

    stats: Optional[CacheStats] = cache.near_cache_stats
    assert stats is not None

    # populate the near cache
    await cache.put("a", "b")
    await cache.get("a")

    assert stats.size == 1
    assert stats.puts == 1
    assert stats.gets == 1
    assert stats.hits == 0
    assert stats.misses == 1
    assert stats.expires == 0

    # blind replace
    await cache.replace("a", "c")

    assert stats.size == 1
    assert stats.puts == 2
    assert stats.gets == 1
    assert stats.hits == 0
    assert stats.misses == 1
    assert stats.expires == 0

    # invalid mapping should have no impact on near cache
    await cache.replace_mapping("a", "b", "c")

    assert stats.size == 1
    assert stats.puts == 2
    assert stats.gets == 1
    assert stats.hits == 0
    assert stats.misses == 1
    assert stats.expires == 0

    # assert near cache entry is removed
    await cache.replace_mapping("a", "c", "b")

    assert stats.size == 1
    assert stats.puts == 3
    assert stats.gets == 1
    assert stats.hits == 0
    assert stats.misses == 1
    assert stats.expires == 0


@pytest.mark.asyncio
async def test_clear(test_session: Session) -> None:
    cache: NamedCache[str, str] = await test_session.get_cache(
        "basic", CacheOptions(near_cache_options=NearCacheOptions(ttl=2000))
    )

    stats: Optional[CacheStats] = cache.near_cache_stats
    assert stats is not None

    await cache.put_all({str(x): str(x) for x in range(10)})

    async for _ in await cache.get_all({str(x) for x in range(10)}):
        continue

    assert stats.size == 10
    assert stats.puts == 10
    assert stats.gets == 10
    assert stats.hits == 0
    assert stats.misses == 10

    await cache.clear()

    assert stats.size == 0
    assert stats.puts == 10
    assert stats.gets == 10
    assert stats.hits == 0
    assert stats.misses == 10


@pytest.mark.asyncio
async def test_incompatible_near_cache_options(test_session: Session) -> None:
    cache: NamedCache[str, str] = await test_session.get_cache(
        "basic", CacheOptions(near_cache_options=NearCacheOptions(ttl=2000))
    )

    with pytest.raises(ValueError) as err:
        await test_session.get_cache("basic", CacheOptions(near_cache_options=NearCacheOptions(ttl=1900)))

    assert str(err.value) == "A NamedMap or NamedCache with the same name already exists with different CacheOptions"

    cache2: NamedCache[str, str] = await test_session.get_cache(
        "basic", CacheOptions(near_cache_options=NearCacheOptions(ttl=2000))
    )

    assert cache == cache2
