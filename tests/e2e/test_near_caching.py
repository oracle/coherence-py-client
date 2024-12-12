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
    await asyncio.sleep(1)
    assert await cache.get("a") == {"b": "c"}

    assert stats.size == 1
    assert stats.puts == 5
    assert stats.gets == 6
    assert stats.hits == 2
    assert stats.misses == 4
    assert stats.expires == 1


@pytest.mark.asyncio
async def test_get_all(test_session: Session) -> None:
    pass


@pytest.mark.asyncio
async def test_remove(test_session: Session) -> None:
    pass


@pytest.mark.asyncio
async def test_contains_key(test_session: Session) -> None:
    pass


@pytest.mark.asyncio
async def test_replace(test_session: Session) -> None:
    pass


@pytest.mark.asyncio
async def test_high_units(test_session: Session) -> None:
    pass


@pytest.mark.asyncio
async def test_high_units_access(test_session: Session) -> None:
    pass


@pytest.mark.asyncio
async def test_high_units_memory(test_session: Session) -> None:
    pass


@pytest.mark.asyncio
async def test_clear(test_session: Session) -> None:
    pass


@pytest.mark.asyncio
async def test_duplicate_cache(test_session: Session) -> None:
    pass


@pytest.mark.asyncio
async def test_incompatible_near_cache_options(test_session: Session) -> None:
    pass
