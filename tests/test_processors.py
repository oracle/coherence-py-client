# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.
import os
from typing import Any, AsyncGenerator, Final

import pytest
import pytest_asyncio

from coherence import NamedCache, Options, Session, TlsOptions
from coherence.extractor import ChainedExtractor, UniversalExtractor
from coherence.filter import AlwaysFilter, EqualsFilter, Filter, NeverFilter, NotFilter, PresentFilter
from coherence.processor import (
    ConditionalProcessor,
    ConditionalPut,
    ConditionalPutAll,
    ConditionalRemove,
    ExtractorProcessor,
    MethodInvocationProcessor,
    NullProcessor,
    NumberIncrementor,
    NumberMultiplier,
    PreloadRequest,
    ScriptProcessor,
    TouchProcessor,
    UpdaterProcessor,
    VersionedPut,
    VersionedPutAll,
    extract,
)
from coherence.serialization import JSONSerializer
from tests.address import Address
from tests.person import Person


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

    r: Any = await cache.invoke(k2, extract("length()"))
    assert r == len(v2)

    r = await cache.invoke(k2, extract("isEmpty()"))
    assert r is False

    r = await cache.invoke(k2, extract("toUpperCase()"))
    assert r == v2.upper()

    k3 = Person.Andy().name
    v3 = Person.Andy()
    await cache.put(k3, v3)
    r = await cache.invoke(k3, ExtractorProcessor(UniversalExtractor("name")))
    assert r == k3
    r = await cache.invoke(k3, ExtractorProcessor(UniversalExtractor("address")))
    assert type(r) == Address
    assert r.zipcode == v3.address.zipcode
    r = await cache.invoke(k3, ExtractorProcessor(ChainedExtractor("address.zipcode")))
    assert r == v3.address.zipcode


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_composite(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[Any, Any] = setup_and_teardown

    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    cp = extract("id").and_then(extract("my_str"))
    r: Any = await cache.invoke(k, cp)
    assert r == [123, "123"]

    k3 = Person.Pat().name
    v3 = Person.Pat()
    await cache.put(k3, v3)
    cp = extract("weight").and_then(extract("address.zipcode"))
    r = await cache.invoke(k3, cp)
    assert r == [Person.Pat().weight, Person.Pat().address.zipcode]


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_conditional(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[Any, Any] = setup_and_teardown

    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f: Filter = EqualsFilter.create(UniversalExtractor.create("id"), 123)
    cp = ConditionalProcessor(f, extract("my_str"))
    r: Any = await cache.invoke(k, cp)
    assert r == "123"

    await cache.put(k, v)
    f = EqualsFilter.create(UniversalExtractor.create("id"), 1234)
    cp = ConditionalProcessor.create(f, extract("my_str"))
    r = await cache.invoke(k, cp)
    assert r is None


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_null(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[Any, Any] = setup_and_teardown

    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    cp = NullProcessor.get_instance()
    r: Any = await cache.invoke(k, cp)
    assert r is True


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_multiplier(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[Any, Any] = setup_and_teardown

    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    cp = NumberMultiplier("ival", 2)
    r: Any = await cache.invoke(k, cp)
    assert r == 246


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_incrementor(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[Any, Any] = setup_and_teardown

    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    cp = NumberIncrementor("ival", 2)
    r: Any = await cache.invoke(k, cp)
    assert r == 125


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_conditional_put(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[Any, Any] = setup_and_teardown

    k1 = "one"
    v1 = "only-one"
    await cache.put(k1, v1)

    f: Filter = NeverFilter()  # This will always return False
    cp = ConditionalPut(f, "only-one-one")
    r: Any = await cache.invoke(k1, cp)
    assert r == v1
    cp = ConditionalPut(f, "only-one-one", False)
    r = await cache.invoke(k1, cp)
    assert r is None

    f = AlwaysFilter()  # This will always return True
    cp = ConditionalPut(f, "only-one-one")
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

    f = AlwaysFilter()  # This will always return True
    cp = ConditionalPutAll(f, dict([(k1, "only-one-one"), (k2, "only-two-two")]))
    await cache.invoke_all(cp)
    assert await cache.get(k1) == "only-one-one"
    assert await cache.get(k2) == "only-two-two"

    pf = PresentFilter()
    cp = ConditionalPutAll(NotFilter(pf), dict([("three", "only-three")]))
    await cache.invoke_all(cp, {"one", "three"})
    assert await cache.get(k1) == "only-one-one"
    assert await cache.get(k2) == "only-two-two"
    assert await cache.get("three") == "only-three"


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_conditional_remove(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[Any, Any] = setup_and_teardown

    k1 = "one"
    v1 = "only-one"
    await cache.put(k1, v1)

    f: Filter = NeverFilter()  # This will always return False
    cp = ConditionalRemove(f)
    r: Any = await cache.invoke(k1, cp)
    assert r == v1
    assert await cache.get(k1) == "only-one"
    cp = ConditionalRemove(f, False)
    r = await cache.invoke(k1, cp)
    assert r is None
    assert await cache.get(k1) == "only-one"

    f = AlwaysFilter()  # This will always return True
    cp = ConditionalRemove(f)
    r = await cache.invoke(k1, cp)
    assert r is None
    assert await cache.get(k1) is None


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_method_invocation(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[Any, Any] = setup_and_teardown

    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    p = MethodInvocationProcessor.create("get", False, "ival")  # Non-mutating form
    r: Any = await cache.invoke(k, p)
    assert r == 123

    p = MethodInvocationProcessor.create("size", False)  # Non-mutating form
    r = await cache.invoke(k, p)
    assert r == 6

    p = MethodInvocationProcessor.create("isEmpty", False)  # Non-mutating form
    r = await cache.invoke(k, p)
    assert r is False

    p = MethodInvocationProcessor.create("remove", True, "ival")  # Mutating form
    r = await cache.invoke(k, p)
    assert r == 123


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_touch() -> None:
    tp = TouchProcessor.create()
    serializer = JSONSerializer()
    j = serializer.serialize(tp)
    json_object: TouchProcessor = serializer.deserialize(j)
    assert json_object is not None
    assert isinstance(json_object, TouchProcessor)


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_script() -> None:
    sp = ScriptProcessor.create("test_script.py", "py", "abc", 2, 4.0)
    serializer = JSONSerializer()
    j = serializer.serialize(sp)
    json_object: ScriptProcessor = serializer.deserialize(j)
    assert json_object is not None
    assert isinstance(json_object, ScriptProcessor)
    assert json_object.name == "test_script.py"
    assert json_object.language == "py"
    assert json_object.args == ["abc", 2, 4.0]


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_preload() -> None:
    tp = PreloadRequest.create()
    serializer = JSONSerializer()
    j = serializer.serialize(tp)
    json_object: PreloadRequest = serializer.deserialize(j)
    assert json_object is not None
    assert isinstance(json_object, PreloadRequest)


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_updater(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[Any, Any] = setup_and_teardown

    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    ep = UpdaterProcessor.create("my_str", "12300").and_then(UpdaterProcessor.create("ival", 12300))
    r: Any = await cache.invoke(k, ep)
    assert r == [True, True]


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_versioned_put(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[Any, Any] = setup_and_teardown

    k = "123"
    versioned123 = {
        "@version": 1,
        "id": 123,
        "my_str": "123",
        "ival": 123,
        "fval": 12.3,
        "iarr": [1, 2, 3],
        "group:": 1,
    }
    versioned123_update = {
        "@version": 1,
        "id": 123,
        "my_str": "123-update",
        "ival": 123,
        "fval": 12.3,
        "iarr": [1, 2, 3],
        "group:": 1,
    }

    expected_result = {
        "@version": 2,
        "id": 123,
        "my_str": "123-update",
        "ival": 123,
        "fval": 12.3,
        "iarr": [1, 2, 3],
        "group:": 1,
    }

    await cache.put(k, versioned123)
    vp = VersionedPut.create(versioned123_update)
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
        "@version": 1,
        "id": 123,
        "my_str": "123",
        "ival": 123,
        "fval": 12.3,
        "iarr": [1, 2, 3],
        "group:": 1,
    }

    versioned123_update = {
        "@version": 1,
        "id": 123,
        "my_str": "123-update",
        "ival": 123,
        "fval": 12.3,
        "iarr": [1, 2, 3],
        "group:": 1,
    }

    expected_versioned123_update = {
        "@version": 2,
        "id": 123,
        "my_str": "123-update",
        "ival": 123,
        "fval": 12.3,
        "iarr": [1, 2, 3],
        "group:": 1,
    }

    k2 = "234"
    versioned234 = {
        "@version": 2,
        "id": 234,
        "my_str": "234",
        "ival": 234,
        "fval": 23.4,
        "iarr": [2, 3, 4],
        "group:": 2,
    }

    versioned234_update = {
        "@version": 2,
        "id": 234,
        "my_str": "234_update",
        "ival": 234,
        "fval": 23.4,
        "iarr": [2, 3, 4],
        "group:": 2,
    }

    expected_versioned234_update = {
        "@version": 3,
        "id": 234,
        "my_str": "234_update",
        "ival": 234,
        "fval": 23.4,
        "iarr": [2, 3, 4],
        "group:": 2,
    }

    await cache.put(k1, versioned123)
    await cache.put(k2, versioned234)

    vpa = VersionedPutAll.create(dict([(k1, versioned123_update), (k2, versioned234_update)]))
    await cache.invoke_all(vpa)
    assert await cache.get(k1) == expected_versioned123_update
    assert await cache.get(k2) == expected_versioned234_update
