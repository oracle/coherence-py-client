# Copyright (c) 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

import asyncio
import time
from functools import reduce

from coherence import CacheOptions, CacheStats, NamedCache, NearCacheOptions, Session


async def do_run() -> None:
    session: Session = await Session.create()

    # obtain the basic cache and configure near caching with
    # all defaults; meaning no expiry or pruning
    cache_remote: NamedCache[str, str] = await session.get_cache("remote")
    cache_near: NamedCache[str, str] = await session.get_cache(
        "near", CacheOptions(near_cache_options=NearCacheOptions(ttl=0))
    )

    await cache_remote.clear()
    await cache_near.clear()
    stats: CacheStats = cache_near.near_cache_stats

    # these knobs control:
    #  - how many current tasks to run
    #  - how many entries will be inserted and queried
    #  - how many times the calls will be invoked
    task_count: int = 25
    num_entries: int = 1_000
    iterations: int = 4

    # seed data to populate the cache
    cache_seed: dict[str, str] = {str(x): str(x) for x in range(num_entries)}
    cache_seed_keys: set[str] = {key for key in cache_seed.keys()}
    print()

    # task calling get_all() for 1_000 keys
    async def get_all_task(task_cache: NamedCache[str, str]) -> int:
        begin = time.time_ns()

        for _ in range(iterations):
            async for _ in await task_cache.get_all(cache_seed_keys):
                continue

        return (time.time_ns() - begin) // 1_000_000

    await cache_remote.put_all(cache_seed)
    await cache_near.put_all(cache_seed)

    print("Run without near caching ...")
    begin_outer: int = time.time_ns()
    results: list[int] = await asyncio.gather(*[get_all_task(cache_remote) for _ in range(task_count)])
    end_outer: int = time.time_ns()
    total_time = end_outer - begin_outer
    task_time = reduce(lambda first, second: first + second, results)

    # Example output
    # Run without near caching ...
    # [remote] 25 tasks completed!
    # [remote] Total time: 4246ms
    # [remote] Tasks completion average: 3755.6

    print(f"[remote] {task_count} tasks completed!")
    print(f"[remote] Total time: {total_time // 1_000_000}ms")
    print(f"[remote] Tasks completion average: {task_time / task_count}")

    print()
    print("Run with near caching ...")
    begin_outer = time.time_ns()
    results = await asyncio.gather(*[get_all_task(cache_near) for _ in range(task_count)])
    end_outer = time.time_ns()
    total_time = end_outer - begin_outer
    task_time = reduce(lambda first, second: first + second, results)

    # Run with near caching ...
    # [near] 25 tasks completed!
    # [near] Total time: 122ms
    # [near] Tasks completion average: 113.96
    # [near] Near cache statistics: CacheStats(puts=1000, gets=100000, hits=99000,
    #     misses=1000, misses-duration=73ms, hit-rate=0.99, prunes=0,
    #     num-pruned=0, prunes-duration=0ms, size=1000, expires=0,
    #     num-expired=0, expires-duration=0ms, memory-bytes=681464)

    print(f"[near] {task_count} tasks completed!")
    print(f"[near] Total time: {total_time // 1_000_000}ms")
    print(f"[near] Tasks completion average: {task_time / task_count}")
    print(f"[near] Near cache statistics: {stats}")

    await session.close()


asyncio.run(do_run())
