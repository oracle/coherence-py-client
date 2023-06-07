# Copyright (c) 2022 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.
import asyncio
import logging.config
import os
from typing import List, TypeVar

import pytest

from coherence.event import MapEvent, MapListener

K = TypeVar("K")
"""Generic type for cache keys"""

V = TypeVar("V")
"""Generic type for cache values"""

# logging configuration for tests
logging.config.fileConfig(fname="tests/logging.conf", disable_existing_loggers=False)
COH_TEST_LOG = logging.getLogger("coherence-test")


class CountingMapListener(MapListener[K, V]):
    """Listener for capturing and storing events for test evaluation."""

    _name: str
    """The logical name for this listener."""

    _counter: int
    """The number of events captured between resets."""

    _inserted: List[MapEvent[K, V]]
    """The captured insert events."""

    _updated: List[MapEvent[K, V]]
    """The captured update events."""

    _deleted: List[MapEvent[K, V]]
    """The captured delete events."""

    _order: List[MapEvent[K, V]]
    """The expected order of events."""

    def __init__(self, name: str):
        """
        Constructs a new CountingMapListener.
        This listener will record the number of insert, update, and delete events
        as well as maintaining the order of received events.
        :param name:  the logical name of this listener (used for debug display purposes)
        """
        super().__init__()
        self._name = name
        self._inserted = []
        self._updated = []
        self._deleted = []
        self._order = []
        self._debug = bool(os.getenv("DEBUG", True))
        self._counter = 0

        self.on_inserted(self._handle_inserted)
        self.on_updated(self._handle_updated)
        self.on_deleted(self._handle_deleted)

    async def wait_for(self, event_count: int, timeout: float = 10.0) -> None:
        """
        Wait for the specified number of events to occur.
        :param event_count:  the expected number of events
        :param timeout:      the maximum time to wait for all events (defaults to 10.0)
        """
        await asyncio.wait_for(asyncio.create_task(self._wait_counter(event_count)), timeout)

    def reset(self) -> None:
        """Resets the listener to its initial state."""
        self._counter = 0
        self._inserted = []
        self._updated = []
        self._deleted = []
        self._order = []

    @property
    def inserted(self) -> List[MapEvent[K, V]]:
        """
        Returns the list of captured insert MapEvents.
        :return: the list of captured insert MapEvents
        """
        return self._inserted

    @property
    def updated(self) -> List[MapEvent[K, V]]:
        """
        Returns the list of captured update MapEvents.
        :return: the list of captured update MapEvents
        """
        return self._updated

    @property
    def deleted(self) -> List[MapEvent[K, V]]:
        """
        Returns the list of captured delete MapEvents.
        :return: the list of captured delete MapEvents
        """
        return self._deleted

    @property
    def order(self) -> List[MapEvent[K, V]]:
        """
        Returns the list of all captured MapEvents in the order received.
        :return: the list of all captured MapEvents in the order received
        """
        return self._order

    @property
    def count(self) -> int:
        """
        Returns the total number of events captured.
        :return: the total number of events captured
        """
        return self._counter

    @property
    def name(self) -> str:
        """
        Returns the logical name of this listener.
        :return:  the logical name of this listener
        """
        return self._name

    def _handle_inserted(self, event: MapEvent[K, V]) -> None:
        """
        Records the insert event.
        :param event:  the insert event
        """
        self._handle_common(event)
        self.inserted.append(event)

    def _handle_updated(self, event: MapEvent[K, V]) -> None:
        """
        Records the update event.
        :param event:  the update event
        """
        self._handle_common(event)
        self.updated.append(event)

    def _handle_deleted(self, event: MapEvent[K, V]) -> None:
        """
        Records the delete event.
        :param event:  the delete event
        """
        self._handle_common(event)
        self.deleted.append(event)

    def _handle_common(self, event: MapEvent[K, V]) -> None:
        """
        Common logic for all events.
        :param event:  the event
        """
        self.order.append(event)
        self._counter += 1
        COH_TEST_LOG.debug("[%s] Received event [%s]", self.name, event)

    async def _wait_counter(self, event_count: int) -> None:
        """
        Loops waiting for the internal counter to equal `event_count`.
        :param event_count:  the number of expected events
        """
        while True:
            if self.count == event_count:
                return
            await asyncio.sleep(0)
