# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from asyncio import Event
from time import sleep, time
from typing import Dict, Final, List, Optional, Set, TypeVar, Union

import pytest

import tests
from coherence import Aggregators, Filters, MapEntry, NamedCache, Session
from coherence.event import MapLifecycleEvent
from coherence.extractor import ChainedExtractor, Extractors, UniversalExtractor
from coherence.processor import ExtractorProcessor
from tests.address import Address
from tests.person import Person

K = TypeVar("K")
V = TypeVar("V")
R = TypeVar("R")


async def _insert_large_number_of_entries(cache: NamedCache[str, str]) -> int:
    # insert enough data into the cache to ensure results will be paged
    # by the proxy.
    num_bulk_ops: int = 10
    num_entries: int = 40000
    bulk_ops: int = int(num_entries / num_bulk_ops)
    to_send: Dict[str, str] = {}
    for i in range(num_bulk_ops):
        offset: int = i * bulk_ops
        for n in range(bulk_ops):
            to_insert: str = str(offset + n)
            to_send[to_insert] = to_insert

        await cache.put_all(to_send)

    return num_entries


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_get_and_put(cache: NamedCache[str, Union[str, int, Person]]) -> None:
    k: str = "one"
    v: str = "only-one"
    # c.put(k, v, 60000)
    await cache.put(k, v)
    r = await cache.get(k)
    assert r == v

    k1: str = "two"
    v1: int = 2
    await cache.put(k1, v1)
    r = await cache.get(k1)
    assert r == v1

    k2: str = Person.andy().name
    v2: Person = Person.andy()
    await cache.put(k2, v2)
    r = await cache.get(k2)
    assert isinstance(r, Person)
    assert r.name == k2
    assert r.address.city == Person.andy().address.city


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_put_with_ttl(cache: NamedCache[str, Union[str, int]]) -> None:
    k: str = "one"
    v: str = "only-one"
    await cache.put(k, v, 5000)  # TTL of 5 seconds
    r = await cache.get(k)
    assert r == v

    sleep(5)  # sleep for 5 seconds
    r = await cache.get(k)
    assert r is None


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_put_if_absent(cache: NamedCache[str, str]) -> None:
    k: str = "one"
    v: str = "only-one"
    await cache.put(k, v)
    k1: str = "two"
    v1: str = "only-two"
    r = await cache.put_if_absent(k1, v1)
    assert r is None

    r = await cache.put_if_absent(k, v)
    assert r == v


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_keys_filtered(cache: NamedCache[str, str]) -> None:
    k: str = "one"
    v: str = "only-one"
    await cache.put(k, v)
    k1: str = "two"
    v1: str = "only-two"
    await cache.put(k1, v1)
    k2: str = "three"
    v2: str = "only-three"
    await cache.put(k2, v2)

    local_set: Set[str] = set()
    async for e in await cache.keys(Filters.equals("length()", 8)):
        local_set.add(e)

    assert len(local_set) == 2
    assert "one" in local_set
    assert "two" in local_set


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_keys_paged(cache: NamedCache[str, str]) -> None:
    # insert enough data into the cache to ensure results will be paged
    # by the proxy.
    num_entries: int = await _insert_large_number_of_entries(cache)

    # Stream the keys and locally cache the results
    local_set: Set[str] = set()
    async for e in await cache.keys(by_page=True):
        local_set.add(e)

    assert len(local_set) == num_entries


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_entries_filtered(cache: NamedCache[str, str]) -> None:
    k: str = "one"
    v: str = "only-one"
    await cache.put(k, v)
    k1: str = "two"
    v1: str = "only-two"
    await cache.put(k1, v1)
    k2: str = "three"
    v2: str = "only-three"
    await cache.put(k2, v2)

    local_dict: Dict[str, str] = {}
    async for e in await cache.entries(Filters.equals("length()", 8)):
        local_dict[e.key] = e.value

    assert len(local_dict) == 2
    assert local_dict["one"] == "only-one"
    assert local_dict["two"] == "only-two"


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_entries_paged(cache: NamedCache[str, str]) -> None:
    # insert enough data into the cache to ensure results will be paged
    # by the proxy.
    num_entries = await _insert_large_number_of_entries(cache)

    assert await cache.size() == num_entries

    # Stream the keys and locally cache the results
    local_dict: Dict[str, str] = {}
    async for e in await cache.entries(by_page=True):
        local_dict[e.key] = e.value

    assert len(local_dict) == num_entries


@pytest.mark.asyncio
async def test_values_filtered(cache: NamedCache[str, str]) -> None:
    k: str = "one"
    v: str = "only-one"
    await cache.put(k, v)
    k1: str = "two"
    v1: str = "only-two"
    await cache.put(k1, v1)
    k2: str = "three"
    v2: str = "only-three"
    await cache.put(k2, v2)

    local_list: List[str] = []
    async for e in await cache.values(Filters.equals("length()", 8)):
        local_list.append(e)

    assert len(local_list) == 2
    assert "only-one" in local_list
    assert "only-two" in local_list


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_values_paged(cache: NamedCache[str, str]) -> None:
    # insert enough data into the cache to ensure results will be paged
    # by the proxy.
    num_entries: int = await _insert_large_number_of_entries(cache)

    # Stream the keys and locally cache the results
    local_list: List[str] = []
    async for e in await cache.values(by_page=True):
        local_list.append(e)

    assert len(local_list) == num_entries


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_put_all(cache: NamedCache[str, str]) -> None:
    k1: str = "three"
    v1: str = "only-three"
    k2: str = "four"
    v2: str = "only-four"
    my_map: Dict[str, str] = {k1: v1, k2: v2}
    await cache.put_all(my_map)
    r1 = await cache.get(k1)
    r2 = await cache.get(k2)
    assert r1 == v1
    assert r2 == v2


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_get_or_default(cache: NamedCache[str, str]) -> None:
    k1: str = "one"
    v1: str = "only-one"
    await cache.put(k1, v1)
    k: str = "five"
    default_v: str = "five-only"
    r: Optional[str] = await cache.get_or_default(k1, default_v)
    assert r == v1
    r2: Optional[str] = await cache.get_or_default(k, default_v)
    assert r2 == default_v


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_get_all(cache: NamedCache[str, str]) -> None:
    k1: str = "one"
    v1: str = "only-one"
    await cache.put(k1, v1)

    k2: str = "two"
    v2: str = "only-two"
    await cache.put(k2, v2)

    k3: str = "three"
    v3: str = "only-three"
    await cache.put(k3, v3)

    r: Dict[str, str] = {}
    # result = await cache.get_all({k1, k3})
    async for e in await cache.get_all({k1, k3}):
        r[e.key] = e.value

    assert r == {k1: v1, k3: v3}


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_get_all_no_keys_raises_error(cache: NamedCache[str, str]) -> None:
    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        await cache.get_all(None)


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_remove(cache: NamedCache[str, str]) -> None:
    k1: str = "one"
    v1: str = "only-one"
    await cache.put(k1, v1)

    r: str = await cache.remove(k1)
    assert r == v1

    r = await cache.remove("some-key")
    assert r is None


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_remove_mapping(cache: NamedCache[str, str]) -> None:
    k1: str = "one"
    v1: str = "only-one"
    await cache.put(k1, v1)

    r: bool = await cache.remove_mapping(k1, v1)
    assert r is True

    r = await cache.remove_mapping("some-key", "some-value")
    assert r is False


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_replace(cache: NamedCache[str, str]) -> None:
    k1: str = "one"
    v1: str = "only-one"
    await cache.put(k1, v1)

    v2: str = "only-one-one"
    r: str = await cache.replace(k1, v2)
    assert r == v1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_replace_mapping(cache: NamedCache[str, str]) -> None:
    k1: str = "one"
    v1: str = "only-one"
    await cache.put(k1, v1)

    v2: str = "only-one-one"
    r: bool = await cache.replace_mapping(k1, v1, v2)
    assert r is True


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_contains_key(cache: NamedCache[str, str]) -> None:
    k1: str = "one"
    v1: str = "only-one"
    await cache.put(k1, v1)

    r: bool = await cache.contains_key(k1)
    assert r is True

    r = await cache.contains_key("two")
    assert r is False


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_contains_value(cache: NamedCache[str, str]) -> None:
    k1: str = "one"
    v1: str = "only-one"
    await cache.put(k1, v1)

    r: bool = await cache.contains_value(v1)
    assert r is True

    r = await cache.contains_key("two-only")
    assert r is False


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_is_empty(cache: NamedCache[str, str]) -> None:
    k1: str = "one"
    v1: str = "only-one"
    await cache.put(k1, v1)

    r: bool = await cache.is_empty()
    assert r is False

    await cache.clear()
    r = await cache.is_empty()
    assert r is True


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_size(cache: NamedCache[str, str]) -> None:
    k1: str = "one"
    v1: str = "only-one"
    await cache.put(k1, v1)
    r: int = await cache.size()
    assert r == 1

    k2: str = "two"
    v2: str = "only-two"
    await cache.put(k2, v2)
    r = await cache.size()
    assert r == 2

    await cache.clear()
    r = await cache.size()
    assert r == 0


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_invoke(cache: NamedCache[str, Union[str, Person]]) -> None:
    k1: str = "one"
    v1: str = "only-one"
    await cache.put(k1, v1)
    k2: str = "two"
    v2: str = "only-two"
    await cache.put(k2, v2)

    r: int = await cache.invoke(k2, ExtractorProcessor(UniversalExtractor("length()")))
    assert r == len(v2)

    r2: bool = await cache.invoke(k2, ExtractorProcessor(UniversalExtractor("isEmpty()")))
    assert r2 is False

    r3: str = await cache.invoke(k2, ExtractorProcessor(UniversalExtractor("toUpperCase()")))
    assert r3 == v2.upper()

    k3: str = Person.andy().name
    v3: Person = Person.andy()
    await cache.put(k3, v3)
    r4: str = await cache.invoke(k3, ExtractorProcessor(UniversalExtractor("name")))
    assert r4 == k3
    r5: Address = await cache.invoke(k3, ExtractorProcessor(UniversalExtractor("address")))
    assert isinstance(r5, Address)
    assert r5.zipcode == v3.address.zipcode
    r6: int = await cache.invoke(k3, ExtractorProcessor(ChainedExtractor("address.zipcode")))
    assert r6 == v3.address.zipcode


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_invoke_all_keys(cache: NamedCache[str, str]) -> None:
    k1: str = "one"
    v1: str = "only-one"
    await cache.put(k1, v1)

    k2: str = "two"
    v2: str = "only-two"
    await cache.put(k2, v2)

    k3: str = "three"
    v3: str = "only-three"
    await cache.put(k3, v3)

    r: Dict[str, int] = {}
    e: MapEntry[str, int]
    async for e in await cache.invoke_all(ExtractorProcessor(UniversalExtractor("length()")), keys={k1, k3}):
        r[e.key] = e.value

    assert r == {k1: 8, k3: 10}


EVENT_TIMEOUT: Final[float] = 20.0


# noinspection PyShadowingNames
@pytest.mark.asyncio(loop_scope="function")
async def test_cache_truncate_event(cache: NamedCache[str, str]) -> None:
    name: str = "UNSET"
    event: Event = Event()

    def callback(n: str) -> None:
        nonlocal name
        name = n
        event.set()

    cache.on(MapLifecycleEvent.TRUNCATED, callback)

    await cache.put("A", "B")
    await cache.put("C", "D")
    assert await cache.size() == 2

    await cache.truncate()
    await tests.wait_for(event, EVENT_TIMEOUT)

    assert name == cache.name
    assert await cache.size() == 0


# noinspection PyShadowingNames,DuplicatedCode
@pytest.mark.asyncio(loop_scope="function")
async def test_cache_release_event() -> None:
    session: Session = await tests.get_session()
    cache: NamedCache[str, str] = await session.get_cache("test-" + str(int(time() * 1000)))
    name: str = "UNSET"
    event: Event = Event()

    def callback(n: str) -> None:
        nonlocal name
        name = n
        event.set()

    cache.on(MapLifecycleEvent.RELEASED, callback)

    try:
        await cache.put("A", "B")
        await cache.put("C", "D")
        assert await cache.size() == 2

        cache.release()
        await tests.wait_for(event, EVENT_TIMEOUT)

        assert name == cache.name
        assert cache.released
        assert not cache.destroyed
        assert not cache.active
    finally:
        await session.close()


# noinspection PyShadowingNames,DuplicatedCode,PyUnresolvedReferences
@pytest.mark.asyncio
async def test_add_remove_index(person_cache: NamedCache[str, Person]) -> None:
    await person_cache.add_index(Extractors.extract("age"))
    result = await person_cache.aggregate(Aggregators.record(), None, Filters.greater("age", 25))
    # print(result)
    # {'@class': 'util.SimpleQueryRecord', 'results': [{'@class': 'util.SimpleQueryRecord.PartialResult',
    # 'partitionSet': {'@class': 'net.partition.PartitionSet', 'bits': [2147483647], 'markedCount': -1,
    # 'partitionCount': 31, 'tailMask': 2147483647}, 'steps': [{'@class': 'util.SimpleQueryRecord.PartialResult.Step',
    # 'efficiency': 5, 'filter': 'GreaterFilter(.age, 25)',
    # 'indexLookupRecords': [{'@class': 'util.SimpleQueryRecord.PartialResult.IndexLookupRecord',
    # 'bytes': 6839, 'distinctValues': 5, 'extractor': '.age', 'index': 'Partitioned: Footprint=6.67KB, Size=5',
    # 'indexDesc': 'Partitioned: ', 'ordered': False}], 'keySetSizePost': 0, 'keySetSizePre': 7, 'millis': 0,
    # 'subSteps': []}]}], 'type': {'@class': 'aggregator.QueryRecorder.RecordType', 'enum': 'EXPLAIN'}}

    idx_rec = result["results"][0].get("steps")[0].get("indexLookupRecords")[0]
    # print(idx_rec)
    # {'@class': 'util.SimpleQueryRecord.PartialResult.IndexLookupRecord', 'bytes': 6839, 'distinctValues': 5,
    # 'extractor': '.age', 'index': 'Partitioned: Footprint=6.67KB, Size=5', 'indexDesc': 'Partitioned: ',
    # 'ordered': False}
    assert "index" in idx_rec

    await person_cache.remove_index(Extractors.extract("age"))
    result2 = await person_cache.aggregate(Aggregators.record(), None, Filters.greater("age", 25))
    print(result2)
    # {'@class': 'util.SimpleQueryRecord', 'results': [{'@class': 'util.SimpleQueryRecord.PartialResult',
    # 'partitionSet': {'@class': 'net.partition.PartitionSet', 'bits': [2147483647], 'markedCount': -1,
    # 'partitionCount': 31, 'tailMask': 2147483647}, 'steps': [{'@class': 'util.SimpleQueryRecord.PartialResult.Step',
    # 'efficiency': 7000, 'filter': 'GreaterFilter(.age, 25)',
    # 'indexLookupRecords': [{'@class': 'util.SimpleQueryRecord.PartialResult.IndexLookupRecord', 'bytes': -1,
    # 'distinctValues': -1, 'extractor': '.age', 'ordered': False}], 'keySetSizePost': 0, 'keySetSizePre': 7,
    # 'millis': 0, 'subSteps': []}]}], 'type': {'@class': 'aggregator.QueryRecorder.RecordType', 'enum': 'EXPLAIN'}}
    idx_rec = result2["results"][0].get("steps")[0].get("indexLookupRecords")[0]
    # print(idx_rec)
    # {'@class': 'util.SimpleQueryRecord.PartialResult.IndexLookupRecord', 'bytes': -1, 'distinctValues': -1,
    # 'extractor': '.age', 'ordered': False}
    assert "index" not in idx_rec
