# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

import os
from decimal import Decimal
from typing import Any, AsyncGenerator, Final, List, cast

import pytest
import pytest_asyncio

from coherence import Aggregators, Filters, NamedCache, Options, Session, TlsOptions
from coherence.aggregator import (
    EntryAggregator,
    PriorityAggregator,
    RecordType,
    ReducerResult,
    Schedule,
    ScriptAggregator,
    Timeout,
    TopAggregator,
)
from coherence.serialization import JSONSerializer
from tests.person import Person


async def get_session() -> Session:
    default_address: Final[str] = "localhost:1408"
    default_scope: Final[str] = ""
    default_request_timeout: Final[float] = 30.0
    default_format: Final[str] = "json"

    run_secure: Final[str] = "RUN_SECURE"
    session: Session = await Session.create()

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
    session: Session = await get_session()
    cache: NamedCache[Any, Any] = await session.get_cache("test")

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

    await cache.clear()
    await cache.destroy()
    await session.close()


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_max(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[str, Person] = setup_and_teardown

    ag: EntryAggregator[int] = Aggregators.max("age")
    r: int = await cache.aggregate(ag)
    assert r == Person.Pat().age


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_min(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[str, Person] = setup_and_teardown

    ag: EntryAggregator[int] = Aggregators.min("age")
    r: int = await cache.aggregate(ag)
    assert r == Person.Alice().age


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_sum(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[str, Person] = setup_and_teardown

    ag = Aggregators.sum("age")
    r = await cache.aggregate(ag)
    assert r == (
        Person.Andy().age
        + Person.Alice().age
        + Person.Pat().age
        + Person.Paula().age
        + Person.Fred().age
        + Person.Fiona().age
        + Person.Jim().age
    )


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_average(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[str, Person] = setup_and_teardown

    ag = Aggregators.average("age")
    r: Decimal = await cache.aggregate(ag)
    assert float(r) == round(
        (
            Person.Andy().age
            + Person.Alice().age
            + Person.Pat().age
            + Person.Paula().age
            + Person.Fred().age
            + Person.Fiona().age
            + Person.Jim().age
        )
        / 7,
        8,
    )


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_count(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[str, Person] = setup_and_teardown

    ag = Aggregators.count()
    r: int = await cache.aggregate(ag)
    assert r == 7


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_distinct_values(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[str, Person] = setup_and_teardown

    ag: EntryAggregator[List[str]] = Aggregators.distinct("gender")
    r: list[str] = await cache.aggregate(ag)
    assert sorted(r) == ["Female", "Male"]


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_top(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[str, Person] = setup_and_teardown

    ag: TopAggregator[int, Person] = Aggregators.top(2).order_by("age").ascending
    r: list[Person] = await cache.aggregate(ag)
    assert r == [Person.Alice(), Person.Andy()]

    ag = Aggregators.top(2).order_by("age").ascending
    r = await cache.aggregate(ag, None, Filters.between("age", 30, 40))
    assert r == [Person.Paula(), Person.Jim()]

    ag = Aggregators.top(2).order_by("age").descending
    r = await cache.aggregate(ag)
    assert r == [Person.Pat(), Person.Fred()]

    ag = Aggregators.top(2).order_by("age").descending
    r = await cache.aggregate(ag, None, Filters.between("age", 20, 30))
    assert r == [Person.Fiona(), Person.Andy()]


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_group(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[str, Person] = setup_and_teardown

    ag: EntryAggregator[dict[str, int]] = Aggregators.group_by("gender", Aggregators.min("age"), Filters.always())

    r: dict[str, int] = await cache.aggregate(ag)
    print("\n" + str(r))
    assert r == {"Male": 25, "Female": 22}

    f = Filters.between("age", 20, 24)
    r = await cache.aggregate(ag, None, f)
    print("\n" + str(r))
    assert r == {"Female": 22}

    r = await cache.aggregate(ag, {"Pat", "Paula", "Fred"})
    print("\n" + str(r))
    assert r == {"Male": 58, "Female": 35}


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_priority(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[str, Person] = setup_and_teardown

    agg: EntryAggregator[Decimal] = Aggregators.priority(Aggregators.sum("age"))
    agg_actual: PriorityAggregator[Decimal] = cast(PriorityAggregator[Decimal], agg)
    assert agg_actual.execution_timeout_in_millis == Timeout.DEFAULT
    assert agg_actual.request_timeout_in_millis == Timeout.DEFAULT
    assert agg_actual.scheduling_priority == Schedule.STANDARD

    r = await cache.aggregate(agg)
    assert r == (
        Person.Andy().age
        + Person.Alice().age
        + Person.Pat().age
        + Person.Paula().age
        + Person.Fred().age
        + Person.Fiona().age
        + Person.Jim().age
    )

    agg2: EntryAggregator[Decimal] = Aggregators.priority(
        Aggregators.sum("age"),
        execution_timeout=Timeout.NONE,
        request_timeout=Timeout.NONE,
        scheduling_priority=Schedule.IMMEDIATE,
    )
    agg2_actual: PriorityAggregator[Decimal] = cast(PriorityAggregator[Decimal], agg2)
    assert agg2_actual.execution_timeout_in_millis == Timeout.NONE
    assert agg2_actual.request_timeout_in_millis == Timeout.NONE
    assert agg2_actual.scheduling_priority == Schedule.IMMEDIATE

    filter = Filters.equals("gender", "Male")
    r = await cache.aggregate(agg, None, filter)
    assert r == (Person.Andy().age + Person.Pat().age + Person.Fred().age + Person.Jim().age)

    r = await cache.aggregate(agg, {"Alice", "Paula", "Fiona"})
    assert r == (Person.Alice().age + Person.Paula().age + Person.Fiona().age)


# noinspection PyShadowingNames
def test_script() -> None:
    agg: EntryAggregator[Any] = Aggregators.script("py", "test_script.py", 0, "abc", 2, 4.0)
    serializer = JSONSerializer()
    j = serializer.serialize(agg)

    script_aggregator: ScriptAggregator[Any] = serializer.deserialize(j)
    assert script_aggregator.name == "test_script.py"
    assert script_aggregator.language == "py"
    assert script_aggregator.args == ["abc", 2, 4.0]
    assert script_aggregator.characteristics == 0


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_query_recorder(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[str, Person] = setup_and_teardown

    agg = Aggregators.record()
    f = Filters.between("age", 20, 30)
    my_result: dict[str, Any | list[Any]] = await cache.aggregate(agg, None, f)
    assert my_result.get("results") is not None
    my_list: Any | list[Any] = my_result.get("results")
    assert len(my_list) == 1
    assert my_list[0].get("partitionSet") is not None
    assert my_list[0].get("steps") is not None

    agg = Aggregators.record(RecordType.TRACE)
    f = Filters.between("age", 20, 30)
    my_result = await cache.aggregate(agg, None, f)
    assert my_result.get("results") is not None
    my_list = my_result.get("results")
    assert len(my_list) == 1  # type: ignore
    assert my_list[0].get("partitionSet") is not None  # type: ignore
    assert my_list[0].get("steps") is not None  # type: ignore


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_reducer(setup_and_teardown: NamedCache[Any, Any]) -> None:
    cache: NamedCache[str, Person] = setup_and_teardown

    agg: EntryAggregator[ReducerResult[str]] = Aggregators.reduce("age")
    f = Filters.between("age", 20, 30)
    my_result: ReducerResult[str] = await cache.aggregate(agg, None, f)
    print("\n" + str(my_result))
    assert my_result == {"Andy": 25, "Fiona": 29, "Alice": 22}

    my_result = await cache.aggregate(agg, {"Andy", "Fiona", "Alice"})
    print("\n" + str(my_result))
    assert my_result == {"Andy": 25, "Alice": 22, "Fiona": 29}
