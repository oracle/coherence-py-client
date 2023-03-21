# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.
import os
from typing import Any, AsyncGenerator, Final

import pytest
import pytest_asyncio

from coherence import NamedCache, Options, Session, TlsOptions
from coherence.extractor import UniversalExtractor
from coherence.filter import (
    BetweenFilter,
    ContainsAllFilter,
    ContainsAnyFilter,
    ContainsFilter,
    EqualsFilter,
    Filters,
    GreaterEqualsFilter,
    GreaterFilter,
    InFilter,
    IsNoneFilter,
    IsNotNoneFilter,
    LessEqualsFilter,
    LessFilter,
    LikeFilter,
    NotEqualsFilter,
    NotFilter,
    PresentFilter,
    RegexFilter,
)
from coherence.processor import ConditionalRemove


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
async def test_and(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache = setup_and_teardown
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = EqualsFilter.create(UniversalExtractor.create("id"), 123).and_(
        EqualsFilter.create(UniversalExtractor.create("my_str"), "123")
    )
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = EqualsFilter.create(UniversalExtractor.create("id"), 1234).and_(
        EqualsFilter.create(UniversalExtractor.create("my_str"), "123")
    )
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_or(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache = setup_and_teardown
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = EqualsFilter.create(UniversalExtractor.create("id"), 123).or_(
        EqualsFilter.create(UniversalExtractor.create("my_str"), "123")
    )
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = EqualsFilter.create(UniversalExtractor.create("id"), 1234).or_(
        EqualsFilter.create(UniversalExtractor.create("my_str"), "1234")
    )
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_xor(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache = setup_and_teardown
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = EqualsFilter.create(UniversalExtractor.create("id"), 123).xor_(
        EqualsFilter.create(UniversalExtractor.create("my_str"), "123")
    )
    cp = ConditionalRemove(f)  # Should fail since filter should return false
    await cache.invoke(k, cp)
    assert await cache.size() == 1

    await cache.put(k, v)
    f = EqualsFilter.create(UniversalExtractor.create("id"), 1234).xor_(
        EqualsFilter.create(UniversalExtractor.create("my_str"), "1234")
    )
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1

    await cache.put(k, v)
    f = EqualsFilter.create(UniversalExtractor.create("id"), 1234).xor_(
        EqualsFilter.create(UniversalExtractor.create("my_str"), "123")
    )
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_all(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache = setup_and_teardown
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f1 = EqualsFilter.create(UniversalExtractor.create("id"), 123)  # True
    f2 = EqualsFilter.create(UniversalExtractor.create("my_str"), "123")  # True
    f3 = EqualsFilter.create(UniversalExtractor.create("ival"), 123)  # True
    all_f = Filters.all([f1, f2, f3])
    cp = ConditionalRemove(all_f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f1 = EqualsFilter.create(UniversalExtractor.create("id"), 123)  # True
    f2 = EqualsFilter.create(UniversalExtractor.create("my_str"), "1234")  # False
    f3 = EqualsFilter.create(UniversalExtractor.create("ival"), 123)  # True
    all_f = Filters.all([f1, f2, f3])
    cp = ConditionalRemove(all_f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_any(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache = setup_and_teardown
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f1 = EqualsFilter.create(UniversalExtractor.create("id"), 1234)  # False
    f2 = EqualsFilter.create(UniversalExtractor.create("my_str"), "1234")  # False
    f3 = EqualsFilter.create(UniversalExtractor.create("ival"), 123)  # True
    all_f = Filters.any([f1, f2, f3])
    cp = ConditionalRemove(all_f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f1 = EqualsFilter.create(UniversalExtractor.create("id"), 1234)  # False
    f2 = EqualsFilter.create(UniversalExtractor.create("my_str"), "1234")  # False
    f3 = EqualsFilter.create(UniversalExtractor.create("ival"), 1234)  # False
    all_f = Filters.any([f1, f2, f3])
    cp = ConditionalRemove(all_f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_greater(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache = setup_and_teardown
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = GreaterFilter.create(UniversalExtractor.create("id"), 122)  # True
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = GreaterFilter.create(UniversalExtractor.create("id"), 123)  # False
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_greater_equals(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache = setup_and_teardown
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = GreaterEqualsFilter.create(UniversalExtractor.create("id"), 122)  # True
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = GreaterEqualsFilter.create(UniversalExtractor.create("id"), 123)  # True
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_less(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache = setup_and_teardown
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = LessFilter.create(UniversalExtractor.create("id"), 124)  # True
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = LessFilter.create(UniversalExtractor.create("id"), 123)  # False
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_less_equals(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache = setup_and_teardown
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = LessEqualsFilter.create(UniversalExtractor.create("id"), 124)  # True
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = LessEqualsFilter.create(UniversalExtractor.create("id"), 123)  # True
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_between(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache = setup_and_teardown
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = BetweenFilter.create(UniversalExtractor.create("id"), 122, 124)
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = BetweenFilter.create(UniversalExtractor.create("id"), 123, 124, True)
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = BetweenFilter.create(UniversalExtractor.create("id"), 122, 123, False, True)
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_not_equals(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache = setup_and_teardown
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = NotEqualsFilter.create(UniversalExtractor.create("id"), 123)  # False
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1

    await cache.put(k, v)
    f = NotEqualsFilter.create(UniversalExtractor.create("id"), 124)  # True
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_not(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache = setup_and_teardown
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = NotFilter.create(EqualsFilter.create(UniversalExtractor.create("id"), 1234))  # True
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = NotFilter.create(EqualsFilter.create(UniversalExtractor.create("id"), 123))  # False
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_is_none(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache = setup_and_teardown
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = IsNoneFilter.create(UniversalExtractor.create("id"))
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1

    await cache.put(k, v)
    f = IsNoneFilter.create(UniversalExtractor.create("id2"))
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_is_not_none(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache = setup_and_teardown
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = IsNotNoneFilter.create(UniversalExtractor.create("id"))
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = IsNotNoneFilter.create(UniversalExtractor.create("id2"))
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_contains_any(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache = setup_and_teardown
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = ContainsAnyFilter.create(UniversalExtractor.create("iarr"), [1, 5, 6])
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = ContainsAnyFilter.create(UniversalExtractor.create("iarr"), [4, 5, 6])
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_contains_all(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache = setup_and_teardown
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = ContainsAllFilter.create(UniversalExtractor.create("iarr"), [1, 2])
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = ContainsAllFilter.create(UniversalExtractor.create("iarr"), [1, 2, 4])
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_contains(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache = setup_and_teardown
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = ContainsFilter.create(UniversalExtractor.create("iarr"), 2)
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = ContainsFilter.create(UniversalExtractor.create("iarr"), 5)
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_in(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache = setup_and_teardown
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = InFilter.create(UniversalExtractor.create("my_str"), ["123", 4, 12.3])
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = InFilter.create(UniversalExtractor.create("ival"), ["123", 4, 12.3])
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_like(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache = setup_and_teardown
    k = "k1"
    v = {"id": 123, "my_str": "123-my-test-string", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = LikeFilter.create(UniversalExtractor.create("my_str"), "123-my-test%")
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = LikeFilter.create(UniversalExtractor.create("my_str"), "123-MY-test%", "0", True)
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = LikeFilter.create(UniversalExtractor.create("my_str"), "123-my-test-s_r_ng")
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_present(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache = setup_and_teardown
    k = "k1"
    v = {"id": 123, "my_str": "123-my-test-string", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = PresentFilter.get_instance()
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = PresentFilter.get_instance()
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke("k2", cp)  # No such key so ConditionalRemove with filter should fail
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_regex(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache = setup_and_teardown
    k = "k1"
    v = {"id": 123, "my_str": "test", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = RegexFilter.create(UniversalExtractor.create("my_str"), "..st")  # 2nd char is 's'
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = RegexFilter.create(UniversalExtractor.create("my_str"), "[ets]+")  # 'ets' occurs more than once
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = RegexFilter.create(UniversalExtractor.create("my_str"), "[aets]*")  # 'aets' occurs zero or more times
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = RegexFilter.create(UniversalExtractor.create("my_str"), "[^abc]")  # '^abc' not a, b or c
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 1
