# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.
from typing import Any

import pytest

from coherence import NamedCache
from coherence.filter import Filters
from coherence.processor import ConditionalRemove, EntryProcessor


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_and(cache: NamedCache[str, Any]) -> None:
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = Filters.equals("id", 123).And(Filters.equals("my_str", "123"))
    cp: EntryProcessor[Any] = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = Filters.equals("id", 1234).And(Filters.equals("my_str", "123"))
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_or(cache: NamedCache[Any, Any]) -> None:
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = Filters.equals("id", 123).Or(Filters.equals("my_str", "123"))
    cp: EntryProcessor[Any] = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = Filters.equals("id", 1234).Or(Filters.equals("my_str", "1234"))
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_xor(cache: NamedCache[Any, Any]) -> None:
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = Filters.equals("id", 123).Xor(Filters.equals("my_str", "123"))
    cp: EntryProcessor[Any] = ConditionalRemove(f)  # Should fail since filter should return false
    await cache.invoke(k, cp)
    assert await cache.size() == 1

    await cache.put(k, v)
    f = Filters.equals("id", 1234).Xor(Filters.equals("my_str", "1234"))
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1

    await cache.put(k, v)
    f = Filters.equals("id", 1234).Xor(Filters.equals("my_str", "123"))
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_all(cache: NamedCache[Any, Any]) -> None:
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f1 = Filters.equals("id", 123)
    f2 = Filters.equals("my_str", "123")
    f3 = Filters.equals("ival", 123)
    all_f = Filters.all([f1, f2, f3])
    cp: EntryProcessor[Any] = ConditionalRemove(all_f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f1 = Filters.equals("id", 123)
    f2 = Filters.equals("my_str", "1234")
    f3 = Filters.equals("ival", 123)
    all_f = Filters.all([f1, f2, f3])
    cp = ConditionalRemove(all_f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_any(cache: NamedCache[Any, Any]) -> None:
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f1 = Filters.equals("id", 1234)  # False
    f2 = Filters.equals("my_str", "1234")  # False
    f3 = Filters.equals("ival", 123)  # True
    all_f = Filters.any([f1, f2, f3])
    cp: EntryProcessor[Any] = ConditionalRemove(all_f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f1 = Filters.equals("id", 1234)  # False
    f2 = Filters.equals("my_str", "1234")  # False
    f3 = Filters.equals("ival", 1234)  # False
    all_f = Filters.any([f1, f2, f3])
    cp = ConditionalRemove(all_f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_greater(cache: NamedCache[Any, Any]) -> None:
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = Filters.greater("id", 122)
    cp: EntryProcessor[Any] = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = Filters.greater("id", 123)
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_greater_equals(cache: NamedCache[Any, Any]) -> None:
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = Filters.greater_equals("id", 122)
    cp: EntryProcessor[Any] = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = Filters.greater_equals("id", 123)
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_less(cache: NamedCache[Any, Any]) -> None:
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = Filters.less("id", 124)
    cp: EntryProcessor[Any] = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = Filters.less("id", 123)
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_less_equals(cache: NamedCache[Any, Any]) -> None:
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = Filters.less_equals("id", 124)
    cp: EntryProcessor[Any] = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = Filters.less_equals("id", 123)
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_between(cache: NamedCache[Any, Any]) -> None:
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = Filters.between("id", 122, 124)
    cp: EntryProcessor[Any] = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = Filters.between("id", 123, 124, True)
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = Filters.between("id", 122, 123, False, True)
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_not_equals(cache: NamedCache[Any, Any]) -> None:
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = Filters.not_equals("id", 123)
    cp: EntryProcessor[Any] = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1

    await cache.put(k, v)
    f = Filters.not_equals("id", 124)
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_not(cache: NamedCache[Any, Any]) -> None:
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = Filters.negate(Filters.equals("id", 1234))
    cp: EntryProcessor[Any] = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = Filters.negate(Filters.equals("id", 123))
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_is_none(cache: NamedCache[Any, Any]) -> None:
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = Filters.is_none("id")
    cp: EntryProcessor[Any] = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1

    await cache.put(k, v)
    f = Filters.is_none("id2")
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_is_not_none(cache: NamedCache[Any, Any]) -> None:
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = Filters.is_not_none("id")
    cp: EntryProcessor[Any] = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = Filters.is_not_none("id2")
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_contains_any(cache: NamedCache[Any, Any]) -> None:
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = Filters.contains_any("iarr", {1, 5, 6})
    cp: EntryProcessor[Any] = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = Filters.contains_any("iarr", {4, 5, 6})
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_contains_all(cache: NamedCache[Any, Any]) -> None:
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = Filters.contains_all("iarr", {1, 2})
    cp: EntryProcessor[Any] = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = Filters.contains_all("iarr", {1, 2, 4})
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_contains(cache: NamedCache[Any, Any]) -> None:
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = Filters.array_contains("iarr", 2)
    cp: EntryProcessor[Any] = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = Filters.array_contains("iarr", 5)
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_in(cache: NamedCache[Any, Any]) -> None:
    k = "k1"
    v = {"id": 123, "my_str": "123", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = Filters.is_in("my_str", {"123", 4, 12.3})
    cp: EntryProcessor[Any] = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = Filters.is_in("ival", {"123", 4, 12.3})
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke(k, cp)
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_like(cache: NamedCache[Any, Any]) -> None:
    k = "k1"
    v = {"id": 123, "my_str": "123-my-test-string", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = Filters.like("my_str", "123-my-test%")
    cp: EntryProcessor[Any] = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = Filters.like("my_str", "123-my-test%", "0", True)
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = Filters.like("my_str", "123-my-test-s_r_ng")
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_present(cache: NamedCache[Any, Any]) -> None:
    k = "k1"
    v = {"id": 123, "my_str": "123-my-test-string", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = Filters.present()
    cp: EntryProcessor[Any] = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = Filters.present()
    cp = ConditionalRemove(f)  # Should fail since filter should return False
    await cache.invoke("k2", cp)  # No such key so ConditionalRemove with filter should fail
    assert await cache.size() == 1


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_regex(cache: NamedCache[Any, Any]) -> None:
    k = "k1"
    v = {"id": 123, "my_str": "test", "ival": 123, "fval": 12.3, "iarr": [1, 2, 3], "group:": 1}
    await cache.put(k, v)
    f = Filters.regex("my_str", "..st")
    cp: EntryProcessor[Any] = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = Filters.regex("my_str", "[ets]+")
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = Filters.regex("my_str", "[aets]*")
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 0

    await cache.put(k, v)
    f = Filters.regex("my_str", "[^abc]")
    cp = ConditionalRemove(f)  # Should pass since filter should return True
    await cache.invoke(k, cp)
    assert await cache.size() == 1
