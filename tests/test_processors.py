# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from typing import Any, AsyncGenerator

import pytest
import pytest_asyncio

import tests
from coherence import MapEntry, NamedCache, Session
from coherence.filter import Filter, Filters
from coherence.processor import EntryProcessor, Numeric, PreloadRequest, Processors, ScriptProcessor, TouchProcessor
from coherence.serialization import JSONSerializer, _META_VERSION
from tests.address import Address
from tests.person import Person


@pytest_asyncio.fixture
async def setup_and_teardown() -> AsyncGenerator[NamedCache[Any, Any], None]:
    session: Session = await tests.get_session()
    cache: NamedCache[Any, Any] = await session.get_cache("test")

    yield cache

    await cache.clear()
    await cache.destroy()
    await session.close()


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_extractor(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[Any, Any] = setup_and_teardown

    k1 = "one"
    v1 = "only-one"
    await cache.put(k1, v1)
    k2 = "two"
    v2 = "only-two"
    await cache.put(k2, v2)

    r: Any = await cache.invoke(k2, Processors.extract("length()"))
    assert r == len(v2)

    r = await cache.invoke(k2, Processors.extract("isEmpty()"))
    assert r is False

    r = await cache.invoke(k2, Processors.extract("toUpperCase()"))
    assert r == v2.upper()

    k3 = Person.andy().name
    v3 = Person.andy()
    await cache.put(k3, v3)
    r = await cache.invoke(k3, Processors.extract("name"))
    assert r == k3
    r = await cache.invoke(k3, Processors.extract("address"))
    assert type(r) == Address
    assert r.zipcode == v3.address.zipcode
    r = await cache.invoke(k3, Processors.extract("address.zipcode"))
    assert r == v3.address.zipcode


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_composite(setup_and_teardown: NamedCache[str, Any]) -> None:
    cache: NamedCache[str, Any] = setup_and_teardown

    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    cp: EntryProcessor[str] = Processors.extract("id").and_then(Processors.extract("my_str"))
    r: Any = await cache.invoke(k, cp)
    assert r == [123, "123"]

    k3 = Person.pat().name
    v3 = Person.pat()
    await cache.put(k3, v3)
    cp = Processors.extract("weight").and_then(Processors.extract("address.zipcode"))
    r = await cache.invoke(k3, cp)
    assert r == [Person.pat().weight, Person.pat().address.zipcode]


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_conditional(setup_and_teardown: NamedCache[str, Any]) -> None:
    cache: NamedCache[str, Any] = setup_and_teardown

    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    ext: EntryProcessor[str] = Processors.extract("my_str")
    cp: EntryProcessor[str] = ext.when(Filters.equals("id", 123))
    r: Any = await cache.invoke(k, cp)
    assert r == "123"

    await cache.put(k, v)
    cp = ext.when(Filters.equals("id", 1234))
    r = await cache.invoke(k, cp)
    assert r is None


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_null(setup_and_teardown: NamedCache[str, Any]) -> None:
    cache: NamedCache[str, Any] = setup_and_teardown

    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    cp: EntryProcessor[bool] = Processors.nop()
    r: Any = await cache.invoke(k, cp)
    assert r is True


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_multiplier(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[Any, Any] = setup_and_teardown

    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    cp: EntryProcessor[Numeric] = Processors.multiply("ival", 2)
    r: Numeric = await cache.invoke(k, cp)
    assert r == 246


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_incrementor(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[Any, Any] = setup_and_teardown

    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    cp = Processors.increment("ival", 2)
    r: Any = await cache.invoke(k, cp)
    assert r == 125


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_conditional_put(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[Any, Any] = setup_and_teardown

    k1 = "one"
    v1 = "only-one"
    await cache.put(k1, v1)

    f: Filter = Filters.never()  # This will always return False
    cp = Processors.conditional_put(f, "only-one-one", True)
    r: Any = await cache.invoke(k1, cp)
    assert r == v1
    cp = Processors.conditional_put(f, "only-one-one", False)
    r = await cache.invoke(k1, cp)
    assert r is None

    f = Filters.always()  # This will always return True
    cp = Processors.conditional_put(f, "only-one-one")
    await cache.invoke(k1, cp)
    assert await cache.get(k1) == "only-one-one"


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_conditional_put_all(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[Any, Any] = setup_and_teardown

    k1 = "one"
    v1 = "only-one"
    await cache.put(k1, v1)

    k2 = "two"
    v2 = "only-two"
    await cache.put(k2, v2)

    f = Filters.always()  # This will always return True
    cp = Processors.conditional_put_all(f, dict([(k1, "only-one-one"), (k2, "only-two-two")]))
    async for _ in cache.invoke_all(cp):
        break  # ignore the results

    assert await cache.get(k1) == "only-one-one"
    assert await cache.get(k2) == "only-two-two"

    pf = Filters.present()
    cp = Processors.conditional_put_all(Filters.negate(pf), dict([("three", "only-three")]))
    async for _ in cache.invoke_all(cp, {"one", "three"}):
        break  # ignore the results

    assert await cache.get(k1) == "only-one-one"
    assert await cache.get(k2) == "only-two-two"
    assert await cache.get("three") == "only-three"


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_conditional_remove(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown

    k1 = "one"
    v1 = "only-one"
    await cache.put(k1, v1)

    f: Filter = Filters.never()  # This will always return False
    cp: EntryProcessor[str] = Processors.conditional_remove(f, True)
    r: str = await cache.invoke(k1, cp)
    assert r == v1
    assert await cache.get(k1) == "only-one"
    cp = Processors.conditional_remove(f)
    r = await cache.invoke(k1, cp)
    assert r is None
    assert await cache.get(k1) == "only-one"

    f = Filters.always()  # This will always return True
    cp = Processors.conditional_remove(f, True)
    r = await cache.invoke(k1, cp)
    assert r is None
    assert await cache.get(k1) is None


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_method_invocation(setup_and_teardown: NamedCache[str, Any]) -> None:
    cache: NamedCache[str, Any] = setup_and_teardown

    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    p: EntryProcessor[str] = Processors.invoke_accessor("get", "ival")  # Non-mutating form
    r: str = await cache.invoke(k, p)
    assert r == 123

    p = Processors.invoke_accessor("size")  # Non-mutating form
    r = await cache.invoke(k, p)
    assert r == 6

    p = Processors.invoke_accessor("isEmpty")  # Non-mutating form
    r = await cache.invoke(k, p)
    assert r is False

    p = Processors.invoke_mutator("remove", "ival")  # Mutating form
    r = await cache.invoke(k, p)
    assert r == 123


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_touch() -> None:
    tp = Processors.touch()
    serializer = JSONSerializer()
    j = serializer.serialize(tp)
    json_object: EntryProcessor[None] = serializer.deserialize(j)
    assert json_object is not None
    assert isinstance(json_object, TouchProcessor)


# noinspection PyShadowingNames,PyUnresolvedReferences
@pytest.mark.asyncio
async def test_script() -> None:
    sp = Processors.script("test_script.py", "py", "abc", 2, 4.0)
    serializer = JSONSerializer()
    j = serializer.serialize(sp)
    json_object: EntryProcessor[Any] = serializer.deserialize(j)
    assert json_object is not None
    assert isinstance(json_object, ScriptProcessor)
    assert json_object.name == "test_script.py"
    assert json_object.language == "py"
    assert json_object.args == ["abc", 2, 4.0]


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_preload() -> None:
    tp = Processors.preload()
    serializer = JSONSerializer()
    j = serializer.serialize(tp)
    json_object: EntryProcessor[None] = serializer.deserialize(j)
    assert json_object is not None
    assert isinstance(json_object, PreloadRequest)


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_updater(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[Any, Any] = setup_and_teardown

    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    ep = Processors.update("my_str", "12300").and_then(Processors.update("ival", 12300))
    r: Any = await cache.invoke(k, ep)
    assert r == [True, True]


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_versioned_put(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[Any, Any] = setup_and_teardown

    k = "123"
    versioned123 = {
        _META_VERSION: 1,
        "id": 123,
        "my_str": "123",
        "ival": 123,
        "fval": 12.3,
        "iarr": [1, 2, 3],
        "group:": 1,
    }
    versioned123_update = {
        _META_VERSION: 1,
        "id": 123,
        "my_str": "123-update",
        "ival": 123,
        "fval": 12.3,
        "iarr": [1, 2, 3],
        "group:": 1,
    }

    expected_result = {
        _META_VERSION: 2,
        "id": 123,
        "my_str": "123-update",
        "ival": 123,
        "fval": 12.3,
        "iarr": [1, 2, 3],
        "group:": 1,
    }

    await cache.put(k, versioned123)
    vp = Processors.versioned_put(versioned123_update)
    r: Any = await cache.invoke(k, vp)
    assert r is None
    result = await cache.get(k)
    assert result == expected_result


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_versioned_put_all(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[Any, Any] = setup_and_teardown
    k1 = "123"
    versioned123 = {
        _META_VERSION: 1,
        "id": 123,
        "my_str": "123",
        "ival": 123,
        "fval": 12.3,
        "iarr": [1, 2, 3],
        "group:": 1,
    }

    versioned123_update = {
        _META_VERSION: 1,
        "id": 123,
        "my_str": "123-update",
        "ival": 123,
        "fval": 12.3,
        "iarr": [1, 2, 3],
        "group:": 1,
    }

    expected_versioned123_update = {
        _META_VERSION: 2,
        "id": 123,
        "my_str": "123-update",
        "ival": 123,
        "fval": 12.3,
        "iarr": [1, 2, 3],
        "group:": 1,
    }

    k2 = "234"
    versioned234 = {
        _META_VERSION: 2,
        "id": 234,
        "my_str": "234",
        "ival": 234,
        "fval": 23.4,
        "iarr": [2, 3, 4],
        "group:": 2,
    }

    versioned234_update = {
        _META_VERSION: 2,
        "id": 234,
        "my_str": "234_update",
        "ival": 234,
        "fval": 23.4,
        "iarr": [2, 3, 4],
        "group:": 2,
    }

    expected_versioned234_update = {
        _META_VERSION: 3,
        "id": 234,
        "my_str": "234_update",
        "ival": 234,
        "fval": 23.4,
        "iarr": [2, 3, 4],
        "group:": 2,
    }

    await cache.put(k1, versioned123)
    await cache.put(k2, versioned234)

    vpa = Processors.versioned_put_all(dict([(k1, versioned123_update), (k2, versioned234_update)]))
    e: MapEntry[Any, Any]
    async for _ in cache.invoke_all(vpa):
        break

    assert await cache.get(k1) == expected_versioned123_update
    assert await cache.get(k2) == expected_versioned234_update
