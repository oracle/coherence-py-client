# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

import asyncio
import time
from typing import Any, AsyncGenerator, Generic, List, TypeVar, cast

import pytest
import pytest_asyncio

import tests
from coherence import Filters, NamedCache, Session
from coherence.event import MapEvent, MapEventType
from coherence.filter import Filter, LessFilter, MapEventFilter
from tests import CountingMapListener
from tests.person import Person

K = TypeVar("K")
"""Generic type for cache keys"""

V = TypeVar("V")
"""Generic type for cache values"""


class ValidateEvent(Generic[K, V]):
    """Simple class to validate expected values against a MapEvent."""

    def __init__(self, name: str, source: NamedCache[K, V], key: K, old: V | None, new: V | None, _type: MapEventType):
        """
        Constructs a new ValidateEvent.
        :param name:    the expected cache name
        :param source:  the expected event source
        :param key:     the expected key
        :param old:     the expected old value, if any
        :param new:     the expected new value, if any
        :param _type:   the MapEventType
        """
        self._name: str = name
        self._source: NamedCache[K, V] = source
        self._key: K = key
        self._old: V | None = old
        self._new: V | None = new
        self._type: MapEventType = _type

    def __str__(self) -> str:
        """
        Returns a string representation of this event.
        :return: a string representation of this event
        """
        return (
            "ValidateEvent{"
            + str(self.type.name)
            + ", cache="
            + str(self.name)
            + ", key="
            + str(self.key)
            + ", old="
            + str(self.old)
            + ", new="
            + str(self.new)
            + "}"
        )

    def equals(self, o: object) -> bool:
        """
        Returns `True` if the comparing against a MapEvent and the MapEvent has the same value for the
        aligned properties, otherwise returns `False`.
        :param o:  the object to test
        :return: `True` if the comparing against a MapEvent and the MapEvent has the same value for the
        aligned properties, otherwise returns `False`
        """
        if isinstance(o, MapEvent):
            event: MapEvent[K, V] = cast(MapEvent[K, V], o)
            return (
                event.name == self.name
                and event.description == self.description
                and event.source == self.source
                and event.key == self.key
                and event.old == self.old
                and event.new == self.new
                and event.type == self.type
            )

        return False

    @property
    def name(self) -> str:
        """
        Returns the expected cache name.
        :return: the expected cache name
        """
        return self._name

    @property
    def description(self) -> str:
        """
        Returns the event's description.
        :return: the event's description
        """
        match self.type:
            case MapEventType.ENTRY_INSERTED:
                return "insert"
            case MapEventType.ENTRY_UPDATED:
                return "update"
            case MapEventType.ENTRY_DELETED:
                return "delete"
            case _:
                return "unknown"

    @property
    def source(self) -> NamedCache[K, V]:
        """
        Returns the expected event source.
        :return: the expected event source
        """
        return self._source

    @property
    def key(self) -> K:
        """
        Returns the expected key.
        :return:  the expected key
        """
        return self._key

    @property
    def old(self) -> V | None:
        """
        Returns the expected old value.
        :return: the expected old value
        """
        return self._old

    @property
    def new(self) -> V | None:
        """
        Returns the expected new value.
        :return: the expected new value
        """
        return self._new

    @property
    def type(self) -> MapEventType:
        """
        Return the expected MapEventType
        :return: the expected MapEventType
        """
        return self._type


class ExpectedEvents(Generic[K, V]):
    """Class for validating expected results against those produced by a CountingMapListener."""

    def __init__(
        self, inserts: List[ValidateEvent[K, V]], updates: List[ValidateEvent[K, V]], deletes: List[ValidateEvent[K, V]]
    ) -> None:
        """
        Constructs a new ExpectedEvents.
        :param inserts: a list of expected inserts
        :param updates: a list of expected updates
        :param deletes: a list of expected deletes
        """
        super().__init__()
        self._inserts: List[ValidateEvent[K, V]] = inserts
        self._updates: List[ValidateEvent[K, V]] = updates
        self._deletes: List[ValidateEvent[K, V]] = deletes

    @property
    def inserts(self) -> List[ValidateEvent[K, V]]:
        """
        Returns the list of expected insert events.
        :return: the list of expected insert events
        """
        return self._inserts

    @property
    def updates(self) -> List[ValidateEvent[K, V]]:
        """
        Returns the list of expected update events.
        :return: the list of expected update events
        """
        return self._updates

    @property
    def deletes(self) -> List[ValidateEvent[K, V]]:
        """
        Returns the list of expected delete events.
        :return: the list of expected delete events
        """
        return self._deletes

    @property
    def total(self) -> int:
        """
        Returns the expected total of events that should be captured.
        :return:  the expected total of events that should be captured
        """
        return self.inserts_count + self.updates_count + self.deletes_count

    @property
    def inserts_count(self) -> int:
        """
        Returns the expected number of insert events.
        :return: the expected number of insert events
        """
        return len(self.inserts)

    @property
    def updates_count(self) -> int:
        """
        Returns the expected number of update events.
        :return: the expected number of update events
        """
        return len(self.updates)

    @property
    def deletes_count(self) -> int:
        """
        Returns the expected number of delete events.
        :return: the expected number of delete events
        """
        return len(self.deletes)

    def validate(self, listener: CountingMapListener[K, V]) -> None:
        """
        Validate the expected events against those captured by the provided listener.
        :param listener: the listener with captured events
        """
        assert listener.count == self.total
        assert len(listener.inserted) == self.inserts_count
        assert len(listener.updated) == self.updates_count
        assert len(listener.deleted) == self.deletes_count

        self.ensure_equal(self.inserts, listener.inserted)
        self.ensure_equal(self.updates, listener.updated)
        self.ensure_equal(self.deletes, listener.deleted)

        ordered_expected: List[ValidateEvent[K, V]] = self.inserts + self.updates + self.deletes
        ordered_actual: List[MapEvent[K, V]] = listener.order
        self.ensure_equal(ordered_expected, ordered_actual)

    @staticmethod
    def ensure_equal(expected: List[ValidateEvent[K, V]], actual: List[MapEvent[K, V]]) -> None:
        """
        Validate event lists are essentially equal.
        :param expected: the expected event list
        :param actual:  the actual event list
        """
        for index, exp in enumerate(expected):
            act: MapEvent[K, V] = actual[index]
            assert exp.equals(act), "Expected [" + str(exp) + "], received: [" + str(act) + "]"


async def _run_basic_test(
    cache: NamedCache[str, str], expected: ExpectedEvents[str, str], filter_mask: int | None = None
) -> None:
    """
    Common logic for basic event tests.
    :param cache:        the cache under test
    :param expected:     the ExpectedEvents for this test
    :param filter_mask:  the event mask, if any
    """
    listener: CountingMapListener[str, str] = CountingMapListener("basic")

    if filter_mask is None:
        await cache.add_map_listener(listener)
    else:
        await cache.add_map_listener(listener, MapEventFilter(filter_mask, Filters.always()))

    await cache.put("A", "B")
    await cache.put("A", "C")
    await cache.remove("A")

    await listener.wait_for(expected.total)

    expected.validate(listener)

    # remove the listener and trigger some events.  Ensure no events captured.
    listener.reset()
    await cache.remove_map_listener(listener)

    await cache.put("A", "B")
    await cache.put("A", "C")
    await cache.remove("A")

    await listener.wait_for(0)

    expected2: ExpectedEvents[str, str] = ExpectedEvents([], [], [])
    expected2.validate(listener)


@pytest_asyncio.fixture
async def setup_and_teardown() -> AsyncGenerator[NamedCache[Any, Any], None]:
    """
    Fixture for test setup/teardown.
    """
    session: Session = await tests.get_session()
    cache: NamedCache[Any, Any] = await session.get_cache("test-" + str(time.time_ns()))

    yield cache

    await cache.clear()
    await cache.destroy()
    await session.close()


# ----- test functions ------------------------------------------------------


@pytest.mark.asyncio
async def test_add_no_listener(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown

    with pytest.raises(ValueError):
        await cache.add_map_listener(None)


@pytest.mark.asyncio
async def test_remove_no_listener(setup_and_teardown: NamedCache[str, str]) -> None:
    cache: NamedCache[str, str] = setup_and_teardown

    with pytest.raises(ValueError):
        await cache.remove_map_listener(None)


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_all(setup_and_teardown: NamedCache[str, str]) -> None:
    """Ensure the registered MapListener is able to receive insert, update, and delete events."""

    cache: NamedCache[str, str] = setup_and_teardown
    name: str = cache.name

    expected: ExpectedEvents[str, str] = ExpectedEvents(
        [ValidateEvent(name, cache, "A", None, "B", MapEventType.ENTRY_INSERTED)],
        [ValidateEvent(name, cache, "A", "B", "C", MapEventType.ENTRY_UPDATED)],
        [ValidateEvent(name, cache, "A", "C", None, MapEventType.ENTRY_DELETED)],
    )

    await _run_basic_test(cache, expected)


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_inserts_only(setup_and_teardown: NamedCache[str, str]) -> None:
    """Ensure the registered MapListener is able to receive insert events only."""

    cache: NamedCache[str, str] = setup_and_teardown
    name: str = cache.name

    expected: ExpectedEvents[str, str] = ExpectedEvents(
        [ValidateEvent(name, cache, "A", None, "B", MapEventType.ENTRY_INSERTED)], [], []
    )

    await _run_basic_test(cache, expected, MapEventFilter.INSERTED)


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_updates_only(setup_and_teardown: NamedCache[str, str]) -> None:
    """Ensure the registered MapListener is able to receive update events only."""

    cache: NamedCache[str, str] = setup_and_teardown
    name: str = cache.name

    expected: ExpectedEvents[str, str] = ExpectedEvents(
        [], [ValidateEvent(name, cache, "A", "B", "C", MapEventType.ENTRY_UPDATED)], []
    )

    await _run_basic_test(cache, expected, MapEventFilter.UPDATED)


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_deletes_only(setup_and_teardown: NamedCache[str, str]) -> None:
    """Ensure the registered MapListener is able to receive delete events only."""

    cache: NamedCache[str, str] = setup_and_teardown
    name: str = cache.name

    expected: ExpectedEvents[str, str] = ExpectedEvents(
        [], [], [ValidateEvent(name, cache, "A", "C", None, MapEventType.ENTRY_DELETED)]
    )

    await _run_basic_test(cache, expected, MapEventFilter.DELETED)


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_multiple_listeners(setup_and_teardown: NamedCache[str, str]) -> None:
    """Ensure the multiple registered MapListeners are able to receive insert, update, and delete events."""

    cache: NamedCache[str, str] = setup_and_teardown
    name: str = cache.name

    expected: ExpectedEvents[str, str] = ExpectedEvents(
        [ValidateEvent(name, cache, "A", None, "B", MapEventType.ENTRY_INSERTED)],
        [ValidateEvent(name, cache, "A", "B", "C", MapEventType.ENTRY_UPDATED)],
        [ValidateEvent(name, cache, "A", "C", None, MapEventType.ENTRY_DELETED)],
    )

    listener: CountingMapListener[str, str] = CountingMapListener("basic")
    listener2: CountingMapListener[str, str] = CountingMapListener("basic")

    await cache.add_map_listener(listener)
    await cache.add_map_listener(listener2)

    await cache.put("A", "B")
    await cache.put("A", "C")
    await cache.remove("A")

    await listener.wait_for(expected.total)
    await listener2.wait_for(expected.total)

    expected.validate(listener)
    expected.validate(listener2)

    # remove the listener and trigger some events.  Ensure no events captured for listener but
    # events captured by the listener2
    listener.reset()
    listener2.reset()
    await cache.remove_map_listener(listener)

    await cache.put("A", "B")
    await cache.put("A", "C")
    await cache.remove("A")

    # give some time for any events
    await asyncio.sleep(1)
    await listener.wait_for(0)
    await listener2.wait_for(expected.total)

    no_events: ExpectedEvents[str, str] = ExpectedEvents([], [], [])
    no_events.validate(listener)

    expected.validate(listener2)

    # remove the remaining listener and trigger some events.  Ensure no events captured.
    listener.reset()
    listener2.reset()
    await cache.remove_map_listener(listener2)

    await cache.put("A", "B")
    await cache.put("A", "C")
    await cache.remove("A")

    # give some time for any events
    await asyncio.sleep(1)
    await listener.wait_for(0)
    await listener2.wait_for(0)

    no_events.validate(listener)
    no_events.validate(listener2)


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_custom_filter_listener(setup_and_teardown: NamedCache[str, Person]) -> None:
    """Ensure a custom filter is applied when filtering values for events."""

    cache: NamedCache[str, Person] = setup_and_teardown
    name: str = cache.name

    fred: Person = Person.fred()
    fiona: Person = Person.fiona()
    pat: Person = Person.pat()

    expected: ExpectedEvents[str, Person] = ExpectedEvents(
        [ValidateEvent(name, cache, "C", None, fiona, MapEventType.ENTRY_INSERTED)],
        [],
        [],
    )

    listener: CountingMapListener[str, Person] = CountingMapListener("basic")
    less_filter: Filter = LessFilter("age", 30)
    no_events: ExpectedEvents[str, Person] = ExpectedEvents([], [], [])

    await cache.add_map_listener(listener, less_filter)

    await cache.put("A", fred)
    await asyncio.sleep(1)
    no_events.validate(listener)

    await cache.put("B", pat)
    await asyncio.sleep(1)
    no_events.validate(listener)

    await cache.put("C", fiona)
    await listener.wait_for(expected.total)
    expected.validate(listener)


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_key_listener(setup_and_teardown: NamedCache[str, Person]) -> None:
    """Ensure a listener can be associated with a key."""

    cache: NamedCache[str, Person] = setup_and_teardown
    name: str = cache.name

    fred: Person = Person.fred()
    fiona: Person = Person.fiona()
    pat: Person = Person.pat()

    expected: ExpectedEvents[str, Person] = ExpectedEvents(
        [ValidateEvent(name, cache, "C", None, fiona, MapEventType.ENTRY_INSERTED)],
        [],
        [],
    )

    listener: CountingMapListener[str, Person] = CountingMapListener("basic")
    no_events: ExpectedEvents[str, Person] = ExpectedEvents([], [], [])

    await cache.add_map_listener(listener, "C")

    await cache.put("A", fred)
    await asyncio.sleep(1)
    no_events.validate(listener)

    await cache.put("B", pat)
    await asyncio.sleep(1)
    no_events.validate(listener)

    await cache.put("C", fiona)
    await listener.wait_for(expected.total)
    expected.validate(listener)


# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_lite_listeners(setup_and_teardown: NamedCache[str, Person]) -> None:
    """Ensure lite event handling works as expected alone or when similar listeners
    are registered that are non-lite.  See test comments for details."""

    cache: NamedCache[str, Person] = setup_and_teardown
    name: str = cache.name
    always: Filter = Filters.always()

    key_listener: CountingMapListener[str, Person] = CountingMapListener("key")
    filter_listener: CountingMapListener[str, Person] = CountingMapListener("filter")
    key_listener_lite: CountingMapListener[str, Person] = CountingMapListener("lite-key")
    filter_listener_lite: CountingMapListener[str, Person] = CountingMapListener("lite-filter")

    await cache.add_map_listener(key_listener_lite, "A", True)
    await cache.add_map_listener(filter_listener_lite, always, True)

    fiona: Person = Person.fiona()

    expected_lite: ExpectedEvents[str, Person] = ExpectedEvents(
        [ValidateEvent(name, cache, "A", None, None, MapEventType.ENTRY_INSERTED)],
        [],
        [],
    )

    expected_non_lite: ExpectedEvents[str, Person] = ExpectedEvents(
        [ValidateEvent(name, cache, "A", None, fiona, MapEventType.ENTRY_INSERTED)],
        [],
        [],
    )

    await cache.put("A", fiona)

    await key_listener_lite.wait_for(expected_lite.total)
    expected_lite.validate(key_listener_lite)

    await filter_listener_lite.wait_for(expected_lite.total)
    expected_lite.validate(filter_listener_lite)

    await cache.clear()
    await asyncio.sleep(1)
    key_listener_lite.reset()
    filter_listener_lite.reset()

    # adding non-lite listeners for same key and filter values
    # should result in non-lite events being returned.
    # From the Coherence docs:
    # Note:
    # Obviously, a lite event's old value and new value may be null.
    # However, even if you request lite events, the old and the new value
    # may be included if there is no additional cost to generate and deliver
    # the event. In other words, requesting that a MapListener receive lite
    # events is simply a hint to the system that the MapListener does
    # not have to know the old and new values for the event.
    await cache.add_map_listener(key_listener, "A")
    await cache.add_map_listener(filter_listener, always)

    await cache.put("A", fiona)

    await key_listener_lite.wait_for(expected_non_lite.total)
    expected_non_lite.validate(key_listener_lite)

    await key_listener.wait_for(expected_non_lite.total)
    expected_non_lite.validate(key_listener)

    await filter_listener_lite.wait_for(expected_non_lite.total)
    expected_non_lite.validate(filter_listener_lite)

    await filter_listener.wait_for(expected_non_lite.total)
    expected_non_lite.validate(filter_listener)

    await cache.clear()
    await asyncio.sleep(1)
    key_listener_lite.reset()
    key_listener.reset()
    filter_listener_lite.reset()
    filter_listener.reset()

    # now, remove the non-lite listeners and ensure lite events are received again
    await cache.remove_map_listener(key_listener, "A")
    await cache.remove_map_listener(filter_listener, always)

    await cache.put("A", fiona)

    await key_listener_lite.wait_for(expected_lite.total)
    expected_lite.validate(key_listener_lite)

    await filter_listener_lite.wait_for(expected_lite.total)
    expected_lite.validate(filter_listener_lite)

    # wait for a few seconds to ensure events didn't come in on the other listeners
    await asyncio.sleep(3)

    assert key_listener.count == 0
    assert filter_listener.count == 0
