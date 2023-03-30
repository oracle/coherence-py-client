# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

import asyncio
import os
from asyncio import Event
from time import time
from typing import Any, AsyncGenerator, Final, Optional, TypeVar

import pytest
import pytest_asyncio

from coherence import Filters, MapEntry, NamedCache, Options, Session, TlsOptions
from coherence.event import MapLifecycleEvent, SessionLifecycleEvent
from coherence.extractor import ChainedExtractor, UniversalExtractor
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
    num_entries: int = 100000
    bulk_ops: int = int(num_entries / num_bulk_ops)
    to_send: dict[str, str] = {}
    for i in range(num_bulk_ops):
        offset: int = i * bulk_ops
        for n in range(bulk_ops):
            to_insert: str = str(offset + n)
            to_send[to_insert] = to_insert

        await cache.put_all(to_send)

    return num_entries


def get_session() -> Session:
    default_address: Final[str] = "localhost:1408"
    default_scope: Final[str] = ""
    default_request_timeout: Final[float] = 30.0
    default_format: Final[str] = "json"

    run_secure: Final[str] = "RUN_SECURE"
    session: Session = Session(None)

    if run_secure in os.environ:
        # Default TlsOptions constructor will pick up the SSL Certs and
        # Key values from these environment variables:
        # COHERENCE_TLS_CERTS_PATH
        # COHERENCE_TLS_CLIENT_CERT
        # COHERENCE_TLS_CLIENT_KEY
        tls_options: TlsOptions = TlsOptions()
        tls_options.enabled = True
        tls_options.locked()

        options: Options = Options(default_address, default_scope, default_request_timeout, default_format)
        options.tls_options = tls_options
        options.channel_options = (("grpc.ssl_target_name_override", "Star-Lord"),)
        session = Session(options)

    return session


@pytest_asyncio.fixture
async def setup_and_teardown() -> AsyncGenerator[NamedCache[Any, Any], None]:
    session: Session = get_session()

    cache: NamedCache[Any, Any] = await session.get_cache("test")

    yield cache  # this is what is returned to the test functions

    await cache.truncate()
    await cache.destroy()
    await session.close()


@pytest_asyncio.fixture
async def setup_and_teardown_person_cache() -> AsyncGenerator[NamedCache[str, Person], None]:
    session: Session = get_session()

    cache: NamedCache[str, Person] = await session.get_cache("test")

    await cache.put(Person.Pat().name, Person.Pat())
    await cache.put(Person.Paula().name, Person.Paula())
    await cache.put(Person.Andy().name, Person.Andy())
    await cache.put(Person.Alice().name, Person.Alice())
    await cache.put(Person.Jim().name, Person.Jim())
    await cache.put(Person.Fred().name, Person.Fred())
    await cache.put(Person.Fiona().name, Person.Fiona())
    print("\n")
    print(Person.Pat())
    print(Person.Paula())
    print(Person.Andy())
    print(Person.Alice())
    print(Person.Jim())
    print(Person.Fred())
    print(Person.Fiona())
    yield cache

    await cache.truncate()
    await cache.destroy()
    await session.close()


@pytest.mark.asyncio
async def test_session_basics() -> None:
    """Test initial session state; CLOSED lifecycle event; and post-close invocations raise error"""

    session: Session = get_session()

    assert session.channel is not None
    assert session.scope == ""
    assert session.options is not None
    assert session.format == "json"
    assert not session.closed

    event: Event = Event()
    session.on(SessionLifecycleEvent.CLOSED, lambda: event.set())
    await session.close()
    await asyncio.wait_for(_waiter(event), 0.5)

    # ensure close is idempotent
    event.clear()
    await session.close()

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(_waiter(event), 0.5)

    assert session.channel is not None
    assert session.scope == ""
    assert session.options is not None
    assert session.format == "json"
    assert session.closed

    with pytest.raises(Exception):
        await session.get_cache("test")

    with pytest.raises(Exception):
        session.on(SessionLifecycleEvent.CLOSED, lambda: None)


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_get_and_put(setup_and_teardown: NamedCache[str, str | int | Person]) -> None:
    cache: NamedCache[str, str | int | Person] = setup_and_teardown

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

    k2: str = Person.Andy().name
    v2: Person = Person.Andy()
    await cache.put(k2, v2)
    r = await cache.get(k2)
    assert type(r) == Person
    assert r.name == k2
    assert r.address.city == Person.Andy().address.city


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_put_if_absent(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown

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
async def test_keys_filtered(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown

    k: str = "one"
    v: str = "only-one"
    await cache.put(k, v)
    k1: str = "two"
    v1: str = "only-two"
    await cache.put(k1, v1)
    k2: str = "three"
    v2: str = "only-three"
    await cache.put(k2, v2)

    local_set: set[str] = set()
    async for e in cache.keys(Filters.equals("length()", 8)):
        local_set.add(e)

    assert len(local_set) == 2
    assert "one" in local_set
    assert "two" in local_set


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_keys_paged(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown

    # insert enough data into the cache to ensure results will be paged
    # by the proxy.
    num_entries: int = await _insert_large_number_of_entries(cache)

    # Stream the keys and locally cache the results
    local_set: set[str] = set()
    async for e in cache.keys():
        local_set.add(e)

    assert len(local_set) == num_entries


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_entries_filtered(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown

    k: str = "one"
    v: str = "only-one"
    await cache.put(k, v)
    k1: str = "two"
    v1: str = "only-two"
    await cache.put(k1, v1)
    k2: str = "three"
    v2: str = "only-three"
    await cache.put(k2, v2)

    local_dict: dict[str, str] = {}
    async for e in cache.entries(Filters.equals("length()", 8)):
        local_dict[e.key] = e.value

    assert len(local_dict) == 2
    assert local_dict["one"] == "only-one"
    assert local_dict["two"] == "only-two"


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_entries_paged(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown

    # insert enough data into the cache to ensure results will be paged
    # by the proxy.
    num_entries = await _insert_large_number_of_entries(cache)

    assert await cache.size() == num_entries

    # Stream the keys and locally cache the results
    local_dict: dict[str, str] = {}
    async for e in cache.entries():
        local_dict[e.key] = e.value

    assert len(local_dict) == num_entries


@pytest.mark.asyncio
async def test_values_filtered(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown

    k: str = "one"
    v: str = "only-one"
    await cache.put(k, v)
    k1: str = "two"
    v1: str = "only-two"
    await cache.put(k1, v1)
    k2: str = "three"
    v2: str = "only-three"
    await cache.put(k2, v2)

    local_list: list[str] = []
    async for e in cache.values(Filters.equals("length()", 8)):
        local_list.append(e)

    assert len(local_list) == 2
    assert "only-one" in local_list
    assert "only-two" in local_list


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_values_paged(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown

    # insert enough data into the cache to ensure results will be paged
    # by the proxy.
    num_entries: int = await _insert_large_number_of_entries(cache)

    # Stream the keys and locally cache the results
    local_list: list[str] = []
    async for e in cache.values():
        local_list.append(e)

    assert len(local_list) == num_entries


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_put_all(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown

    k1: str = "three"
    v1: str = "only-three"
    k2: str = "four"
    v2: str = "only-four"
    my_map: dict[str, str] = {k1: v1, k2: v2}
    await cache.put_all(my_map)
    r1 = await cache.get(k1)
    r2 = await cache.get(k2)
    assert r1 == v1
    assert r2 == v2


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_get_or_default(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown

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
async def test_get_all(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown

    k1: str = "one"
    v1: str = "only-one"
    await cache.put(k1, v1)

    k2: str = "two"
    v2: str = "only-two"
    await cache.put(k2, v2)

    k3: str = "three"
    v3: str = "only-three"
    await cache.put(k3, v3)

    r: dict[str, str] = {}
    async for e in cache.get_all({k1, k3}):
        r[e.key] = e.value

    assert r == {k1: v1, k3: v3}


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_get_all_no_keys_raises_error(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown

    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        await cache.get_all(None)  # type: ignore


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_remove(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown

    k1: str = "one"
    v1: str = "only-one"
    await cache.put(k1, v1)

    r: str = await cache.remove(k1)
    assert r == v1

    r = await cache.remove("some-key")
    assert r is None


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_remove_mapping(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown

    k1: str = "one"
    v1: str = "only-one"
    await cache.put(k1, v1)

    r: bool = await cache.remove_mapping(k1, v1)
    assert r is True

    r = await cache.remove_mapping("some-key", "some-value")
    assert r is False


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_replace(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown

    k1: str = "one"
    v1: str = "only-one"
    await cache.put(k1, v1)

    v2: str = "only-one-one"
    r: str = await cache.replace(k1, v2)
    assert r == v1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_replace_mapping(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown

    k1: str = "one"
    v1: str = "only-one"
    await cache.put(k1, v1)

    v2: str = "only-one-one"
    r: bool = await cache.replace_mapping(k1, v1, v2)
    assert r is True


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_contains_key(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown

    k1: str = "one"
    v1: str = "only-one"
    await cache.put(k1, v1)

    r: bool = await cache.contains_key(k1)
    assert r is True

    r = await cache.contains_key("two")
    assert r is False


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_contains_value(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown

    k1: str = "one"
    v1: str = "only-one"
    await cache.put(k1, v1)

    r: bool = await cache.contains_value(v1)
    assert r is True

    r = await cache.contains_key("two-only")
    assert r is False


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_is_empty(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown

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
async def test_size(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown

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
async def test_invoke(setup_and_teardown: NamedCache[str, str | Person]) -> None:
    cache: NamedCache[str, str | Person] = setup_and_teardown

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

    k3: str = Person.Andy().name
    v3: Person = Person.Andy()
    await cache.put(k3, v3)
    r4: str = await cache.invoke(k3, ExtractorProcessor(UniversalExtractor("name")))
    assert r4 == k3
    r5: Address = await cache.invoke(k3, ExtractorProcessor(UniversalExtractor("address")))
    assert type(r5) == Address
    assert r5.zipcode == v3.address.zipcode
    r6: int = await cache.invoke(k3, ExtractorProcessor(ChainedExtractor("address.zipcode")))
    assert r6 == v3.address.zipcode


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_invoke_all_keys(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown

    k1: str = "one"
    v1: str = "only-one"
    await cache.put(k1, v1)

    k2: str = "two"
    v2: str = "only-two"
    await cache.put(k2, v2)

    k3: str = "three"
    v3: str = "only-three"
    await cache.put(k3, v3)

    r: dict[str, int] = {}
    e: MapEntry[str, int]
    async for e in cache.invoke_all(ExtractorProcessor(UniversalExtractor("length()")), keys={k1, k3}):  # type: ignore
        r[e.key] = e.value

    assert r == {k1: 8, k3: 10}


EVENT_TIMEOUT: Final[float] = 20.0


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_cache_truncate_event(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown
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
    await asyncio.wait_for(_waiter(event), EVENT_TIMEOUT)

    assert name == cache.name
    assert await cache.size() == 0


# noinspection PyShadowingNames,DuplicatedCode
@pytest.mark.asyncio
async def test_cache_release_event() -> None:
    session: Session = get_session()
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
        await asyncio.wait_for(_waiter(event), EVENT_TIMEOUT)

        assert name == cache.name
        assert cache.released
        assert not cache.destroyed
        assert not cache.active
    finally:
        await session.close()


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_cache_destroy_event() -> None:
    session: Session = get_session()
    cache: NamedCache[str, str] = await session.get_cache("test-" + str(int(time() * 1000)))
    name: str = "UNSET"
    event: Event = Event()

    def callback(n: str) -> None:
        nonlocal name
        name = n
        event.set()

    cache.on(MapLifecycleEvent.DESTROYED, callback)

    try:
        await cache.put("A", "B")
        await cache.put("C", "D")
        assert await cache.size() == 2

        await cache.destroy()
        await asyncio.wait_for(_waiter(event), EVENT_TIMEOUT)

        assert name == cache.name
        assert not cache.released
        assert cache.destroyed
        assert not cache.active
    finally:
        await session.close()


# noinspection PyShadowingNames,DuplicatedCode
@pytest.mark.asyncio
async def test_session_release_event() -> None:
    session: Session = get_session()
    cache: NamedCache[str, str] = await session.get_cache("test-" + str(int(time() * 1000)))
    name: str = "UNSET"
    event: Event = Event()

    def callback(n: str) -> None:
        nonlocal name
        name = n
        event.set()

    session.on(MapLifecycleEvent.RELEASED, callback)

    try:
        await cache.put("A", "B")
        await cache.put("C", "D")
        assert await cache.size() == 2

        cache.release()
        await asyncio.wait_for(_waiter(event), EVENT_TIMEOUT)

        assert name == cache.name
        assert cache.released
        assert not cache.destroyed
        assert not cache.active
    finally:
        await session.close()


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_session_destroy_event() -> None:
    session: Session = get_session()
    cache: NamedCache[str, str] = await session.get_cache("test-" + str(int(time() * 1000)))
    name: str = "UNSET"
    event: Event = Event()

    def callback(n: str) -> None:
        nonlocal name
        name = n
        event.set()

    session.on(MapLifecycleEvent.DESTROYED, callback)

    try:
        await cache.put("A", "B")
        await cache.put("C", "D")
        assert await cache.size() == 2

        await cache.destroy()
        await asyncio.wait_for(_waiter(event), EVENT_TIMEOUT)

        assert name == cache.name
        assert not cache.released
        assert cache.destroyed
        assert not cache.active
    finally:
        await session.close()


async def _waiter(event: Event) -> None:
    await event.wait()
