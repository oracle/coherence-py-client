# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

import asyncio
from abc import ABC, ABCMeta, abstractmethod
from asyncio import Event, Task
from enum import Enum, unique
from typing import Any, Callable, Generic, Optional, Set, TypeVar, cast

# noinspection PyPackageRequirements
import grpc
from pymitter import EventEmitter

import coherence.client

from .cache_service_messages_v1_pb2 import MapEventMessage, NamedCacheRequest
from .filter import Filter, Filters, MapEventFilter
from .messages_pb2 import MapEventResponse, MapListenerRequest, MapListenerResponse
from .serialization import Serializer
from .services_pb2_grpc import NamedCacheServiceStub
from .util import RequestFactory, RequestFactoryV1

K = TypeVar("K")
"""the type of the map entry keys."""

V = TypeVar("V")
"""the type of the map entry values."""

RT = TypeVar("RT")
"""the gRPC request type."""


@unique
class MapEventType(Enum):
    """Enum of possible events that could raise a MapEvent."""

    ENTRY_INSERTED = "insert"
    """This event indicates that an entry has been added to the cache."""

    ENTRY_UPDATED = "update"
    """This event indicates that an entry has been updated in the cache."""

    ENTRY_DELETED = "delete"
    """This event indicates that an entry has been removed from the cache."""


@unique
class MapLifecycleEvent(Enum):
    """Enum of possible events that may be raised at different
    points of the cache lifecycle."""

    DESTROYED = "map_destroyed"
    """Raised when a storage for a given cache is destroyed
     (usually as a result of a call to NamedMap.destroy())."""

    TRUNCATED = "map_truncated"
    """Raised when a storage for a given cache is truncated
     as a result of a call to NamedMap.truncate()."""

    RELEASED = "map_released"
    """Raised when the local resources for a cache has been
    released as a result of a call to NamedMap.release().
    Entries within the cache remain untouched"""


@unique
class SessionLifecycleEvent(Enum):
    """Enum of possible events that may be raised at different
    points of the session lifecycle."""

    CONNECTED = "session_connected"
    """Raised when the session has connected."""

    DISCONNECTED = "session_disconnected"
    """Raised when the session has disconnected."""

    RECONNECTED = "session_reconnected"
    """Raised when the session has re-connected."""

    CLOSED = "session_closed"
    """Raised when the session has been closed."""


class MapEvent(Generic[K, V]):
    """An event which indicates that the content of a map has changed:

    * an entry has been added
    * an entry has been removed
    * an entry has been changed
    """

    def __init__(
        self,
        source: coherence.client.NamedMap[K, V],
        response: MapEventResponse | MapEventMessage,
        serializer: Serializer,
    ) -> None:
        """
        Constructs a new MapEvent.
        :param source:      the event source
        :param response:    the MapListenerResponse sent from the server
        :param serializer:  the Serializer that should be used to deserialize event keys and values
        """
        self._key: Optional[K] = None
        self._new_value: Optional[V] = None
        self._old_value: Optional[V] = None
        self._id: MapEventType = self._from_event_id(response.id)
        self._name: str = source.name
        self._source: coherence.client.NamedMap[K, V] = source
        self._serializer: Serializer = serializer
        self._key_bytes: bytes = response.key
        self._new_value_bytes: bytes = response.newValue
        self._old_value_bytes: bytes = response.oldValue

    @property
    def source(self) -> coherence.client.NamedMap[K, V]:
        """
        The source of the event.
        :return: the event source
        """
        return self._source

    @property
    def name(self) -> str:
        """
        The name of the cache from which the event originated.
        :return:  the cache name from which the event originated
        """
        return self._name

    @property
    def description(self) -> str:
        """
        Returns the event's description.
        :return: the event's description
        """
        if self.type == MapEventType.ENTRY_INSERTED:
            return "insert"
        elif self.type == MapEventType.ENTRY_UPDATED:
            return "update"
        elif self.type == MapEventType.ENTRY_DELETED:
            return "delete"
        else:
            return "unknown"

    @property
    def type(self) -> MapEventType:
        """
        The MapEventType.  This may be one of:
        * MapEventType.ENTRY_INSERTED
        * MapEventType.ENTRY_UPDATED
        * MapEventType.ENTRY_DELETED
        :return: the event type
        """
        return self._id

    @property
    def key(self) -> K:
        """
        Return the key for the entry generating the event.
        :return: the key for the entry generating the event
        """
        if self._key is None:
            self._key = self._serializer.deserialize(self._key_bytes)

        return self._key

    @property
    def new(self) -> Optional[V]:
        """
        Return the new value for the entry generating the event.
        :return: the new value, if any, for the entry generating the event
        """
        if self._new_value is None and self._new_value_bytes is not None:
            self._new_value = self._serializer.deserialize(self._new_value_bytes)

        return self._new_value

    @property
    def old(self) -> Optional[V]:
        """
        Return the old value for the entry generating the event.
        :return:the old value, if any, for the entry generating the event
        """
        if self._old_value is None and self._old_value_bytes is not None:
            self._old_value = self._serializer.deserialize(self._old_value_bytes)

        return self._old_value

    def __str__(self) -> str:
        """
        Returns a string representation of this event.
        :return: a string representation of this event
        """
        return (
            "MapEvent{"
            + str(self.type.name)
            + ", cache="
            + self.name
            + ", key="
            + str(self.key)
            + ", old="
            + str(self.old)
            + ", new="
            + str(self.new)
            + "}"
        )

    @staticmethod
    def _from_event_id(_id: int) -> MapEventType:
        """Return the MapEventType based on the on-wire value for the event."""
        if _id == 1:
            return MapEventType.ENTRY_INSERTED
        elif _id == 2:
            return MapEventType.ENTRY_UPDATED
        elif _id == 3:
            return MapEventType.ENTRY_DELETED
        else:
            raise RuntimeError("Unhandled MapEventType [" + str(_id) + "]")


MapListenerCallback = Callable[[MapEvent[K, V]], None]
"""A type alias for MapEventListener callback functions."""


class MapListener(Generic[K, V]):
    """A listener interface for receiving MapEvents."""

    _emitter: EventEmitter
    """The internal emitter used to emit events."""

    def __init__(self) -> None:
        """Constructs a new MapListener."""
        self._emitter = EventEmitter()

    def _on(self, event: MapEventType, callback: MapListenerCallback[K, V]) -> MapListener[K, V]:
        """
        Define a callback for the specified event type.

        :param event:     the event type of interest
        :param callback:  the callback that will be invoked when the specified event has occurred
        """
        self._emitter.on(str(event.value), callback)
        return self

    def on_inserted(self, callback: MapListenerCallback[K, V]) -> MapListener[K, V]:
        """
        Defines the callback that should be invoked when an insertion event has occurred.

        :param callback:  the callback that will be invoked when an insertion event has occurred
        """
        return self._on(MapEventType.ENTRY_INSERTED, callback)

    def on_updated(self, callback: MapListenerCallback[K, V]) -> MapListener[K, V]:
        """
        Defines the callback that should be invoked when an update event has occurred.

        :param callback:  the callback that will be invoked when an update event has occurred
        """
        return self._on(MapEventType.ENTRY_UPDATED, callback)

    def on_deleted(self, callback: MapListenerCallback[K, V]) -> MapListener[K, V]:
        """
        Defines the callback that should be invoked when a deletion event has occurred.

        :param callback:  the callback that will be invoked when a deletion event has occurred
        """
        return self._on(MapEventType.ENTRY_DELETED, callback)

    def on_any(self, callback: MapListenerCallback[K, V]) -> MapListener[K, V]:
        """
        Defines the callback that should be invoked when any entry event has occurred.

        :param callback:  the callback that will be invoked when a deletion event has occurred
        """
        return self.on_deleted(callback).on_updated(callback).on_inserted(callback)


class _ListenerGroup(Generic[K, V, RT], metaclass=ABCMeta):
    _key_or_filter: K | Filter
    """The key or Filter for which this group of listeners will receive events."""

    _registered_lite: bool
    """The flag indicating if any listeners have been registered as lite."""

    _listeners: dict[MapListener[K, V], bool]
    """A map of listeners and associated lite flag."""

    _lite_false_count: int
    """The number of callbacks that aren't lite."""

    _subscription_waiter: Event
    """Used by a caller to be notified when the listener subscription as been completed."""

    _unsubscription_waiter: Event
    """Used by a caller to be notified when the listener unsubscribe as been completed."""

    def __init__(self, key_or_filter: K | Filter) -> None:
        self._key_or_filter = key_or_filter
        self._listeners = {}
        self._lite_false_count = 0
        self._registered_lite = False
        self._subscribed_waiter = Event()
        self._unsubscribed_waiter = Event()

    @abstractmethod
    async def _subscribe(self, lite: bool) -> None:
        pass

    @abstractmethod
    async def _unsubscribe(self) -> None:
        pass

    @abstractmethod
    def _post_subscribe(self, request: RT) -> None:
        """
        Custom actions that implementations may need to make after a subscription has been completed.
        :param request:  the request that was used to subscribe
        """
        pass

    @abstractmethod
    def _post_unsubscribe(self, request: RT) -> None:
        """
        Custom actions that implementations may need to make after an unsubscription has been completed.
        :param request:  the request that was used to unsubscribe
        """
        pass

    @abstractmethod
    def _subscribe_complete(self) -> None:
        pass

    async def add_listener(self, listener: MapListener[K, V], lite: bool) -> None:
        """
        Add a callback to this group. This causes a subscription message to be sent through the stream
        if (a) either this is the first callback, or (b) the lite param is false but all
        the previous callback have lite == True.
        :param listener:  the MapListener to add/subscribe
        :param lite:      `True` if the event should only include the key, or `False`
                           if the event should include old and new values as well as the key
        """
        listeners: dict[MapListener[K, V], bool] = self._listeners
        prev_lite_status: Optional[bool] = listeners.get(listener, None)
        if prev_lite_status is not None and prev_lite_status == lite:
            return

        listeners[listener] = lite

        if not lite:
            self._lite_false_count += 1

        size: int = len(listeners)
        requires_registration: bool = size == 1 or self._registered_lite and not lite

        if requires_registration:
            self._registered_lite = lite
            if size > 1:
                await self._unsubscribe()

            await self._subscribe(lite)

    async def remove_listener(self, listener: MapListener[K, V]) -> None:
        """
        Remove the specified listener from this group.
        :param listener:  the listener to remove
        """
        listeners: dict[MapListener[K, V], bool] = self._listeners
        prev_lite_status: Optional[bool] = self._listeners.get(listener, None)
        if prev_lite_status is not None and prev_lite_status or len(listeners) == 0:
            return

        del listeners[listener]

        if len(listeners) == 0:
            await self._unsubscribe()
            return

        if not prev_lite_status:
            self._lite_false_count -= 1

            if self._lite_false_count == 0:
                await self._unsubscribe()
                await self._subscribe(True)

    # noinspection PyProtectedMember
    def _notify_listeners(self, event: MapEvent[K, V]) -> None:
        """
        Notify all listeners within this group of the provided event.
        :param event:
        """
        event_label: str = self._get_emitter_label(event)
        listener: MapListener[K, V]
        for listener in self._listeners.keys():
            listener._emitter.emit(event_label, event)

    # noinspection PyProtectedMember
    @staticmethod
    def _get_emitter_label(event: MapEvent[K, V]) -> str:
        """
        The string label required by the internal event emitter.
        :param event:  the MapEvent whose label will be generated
        :return: the emitter-friendly event label
        """
        if event.type == MapEventType.ENTRY_DELETED:
            return MapEventType.ENTRY_DELETED.value
        elif event.type == MapEventType.ENTRY_INSERTED:
            return MapEventType.ENTRY_INSERTED.value
        elif event.type == MapEventType.ENTRY_UPDATED:
            return MapEventType.ENTRY_UPDATED.value
        else:
            raise AssertionError(f"Unknown EventType [{event}]")


class _ListenerGroupV0(_ListenerGroup[K, V, MapListenerRequest], metaclass=ABCMeta):
    """Manages a collection of MapEventListeners that will be notified when an event is raised.
    This also manages the on-wire activities for registering/de-registering a listener with the
    gRPC proxy."""

    _manager: _MapEventsManagerV0[K, V]
    """The associated MapEventsManager for this group."""

    _request: MapListenerRequest
    """The subscription request.  A reference is maintained for unsubscribe purposes."""

    def __init__(self, manager: _MapEventsManagerV0[K, V], key_or_filter: K | Filter) -> None:
        """
        Constructs a new _ListenerGroup.
        :param manager:        the _MapEventManager
        :param key_or_filter:  the key or filter for this group of listeners
        :raises ValueError:    if either `manager` or `key_or_filter` is `None`
        """
        if manager is None:
            raise ValueError("Argument `manager` must not be None")
        if key_or_filter is None:
            raise ValueError("Argument `key_or_filter` must not be None")

        super().__init__(key_or_filter=key_or_filter)

        self._manager = manager

    # noinspection PyProtectedMember
    async def _write(self, request: MapListenerRequest) -> None:
        """Write the request to the event stream."""
        event_stream: grpc.aio.StreamStreamCall = await self._manager._ensure_stream()
        await event_stream.write(request)

    # noinspection PyProtectedMember
    async def _subscribe(self, lite: bool) -> None:
        """
        Send a gRPC MapListener subscription request for a key or filter.
        :param lite:  `True` if the event should only include the key, or `False`
                      if the event should include old and new values as well as the key
        """
        request: MapListenerRequest
        if isinstance(self._key_or_filter, Filter):
            request = self._manager._request_factory.map_listener_request(True, lite, filter=self._key_or_filter)
        else:
            request = self._manager._request_factory.map_listener_request(True, lite, key=self._key_or_filter)

        self._request = request

        # set this registration as pending
        self._manager._pending_registrations[request.uid] = self

        await self._write(request)

        await self._subscribed_waiter.wait()
        self._subscribed_waiter.clear()

    # noinspection PyProtectedMember
    async def _unsubscribe(self) -> None:
        """
        Send a gRPC MapListener request to unsubscribe a listener for a key or filter.
        """

        request: MapListenerRequest
        if isinstance(self._key_or_filter, MapEventFilter):
            request = self._manager._request_factory.map_listener_request(False, filter=self._key_or_filter)
        else:
            request = self._manager._request_factory.map_listener_request(False, key=self._key_or_filter)

        request.filterId = self._request.filterId
        await self._write(request)
        self._post_unsubscribe(request)

    # noinspection PyProtectedMember
    def _subscribe_complete(self) -> None:
        del self._manager._pending_registrations[self._request.uid]
        self._post_subscribe(self._request)

        # notify caller that subscription is active
        self._subscribed_waiter.set()


class _ListenerGroupV1(_ListenerGroup[K, V, NamedCacheRequest], ABC):

    def __init__(self, manager: _MapEventsManagerV1[K, V], key_or_filter: K | Filter):
        if manager is None:
            raise ValueError("Argument `manager` must not be None")
        if key_or_filter is None:
            raise ValueError("Argument `key_or_filter` must not be None")

        super().__init__(key_or_filter=key_or_filter)

        self._manager = manager

    async def _subscribe(self, lite: bool) -> None:
        """
        Send a gRPC MapListener subscription request for a key or filter.
        :param lite:  `True` if the event should only include the key, or `False`
                      if the event should include old and new values as well as the key
        """
        request: NamedCacheRequest
        filter_id: int
        if isinstance(self._key_or_filter, Filter):
            (request, filter_id) = self._manager.request_factory.map_listener_request(
                True, lite, filter=self._key_or_filter
            )
        else:
            (request, filter_id) = self._manager.request_factory.map_listener_request(
                True, lite, key=self._key_or_filter
            )

        self._request = request
        self._filter_id = filter_id

        # set this registration as pending
        self._manager._pending_registrations[filter_id] = self

        await self._manager._named_map._dispatch_and_wait(request)

        self._subscribe_complete()

    async def _unsubscribe(self) -> None:
        request: NamedCacheRequest
        if isinstance(self._key_or_filter, MapEventFilter):
            request = self._manager.request_factory.map_listener_request(
                subscribe=False, filter=self._key_or_filter, filter_id=self._filter_id
            )[0]
        else:
            request = self._manager.request_factory.map_listener_request(subscribe=False, key=self._key_or_filter)[0]

        await self._manager._named_map._dispatch_and_wait(request)
        self._post_unsubscribe(request)

    def _subscribe_complete(self) -> None:
        del self._manager._pending_registrations[self._filter_id]
        self._post_subscribe(self._request)


class _KeyListenerGroupV0(_ListenerGroupV0[K, V]):
    """A ListenerGroup for key-based MapListeners"""

    def __init__(self, manager: _MapEventsManagerV0[K, V], key: K) -> None:
        """
        Creates a new _KeyListenerGroup
        :param manager:  the _MapEventManager
        :param key:      the group key
        """
        super().__init__(manager, key)

    # noinspection PyProtectedMember
    def _post_subscribe(self, request: MapListenerRequest) -> None:
        manager: _MapEventsManager[K, V] = self._manager
        key: K = manager._serializer.deserialize(request.key)
        self._manager._key_group_subscribed(key, self)

    # noinspection PyProtectedMember
    def _post_unsubscribe(self, request: MapListenerRequest) -> None:
        manager: _MapEventsManager[K, V] = self._manager
        key: K = manager._serializer.deserialize(request.key)
        manager._key_group_unsubscribed(key)


class _KeyListenerGroupV1(_ListenerGroupV1[K, V]):
    _manager: _MapEventsManagerV1[K, V]
    """The associated MapEventsManager for this group."""

    _request: MapListenerRequest
    """The subscription request.  A reference is maintained for unsubscribe purposes."""

    def __init__(self, manager: _MapEventsManagerV1[K, V], key_or_filter: K | Filter) -> None:
        """
        Constructs a new _ListenerGroup.
        :param manager:        the _MapEventManager
        :param key_or_filter:  the key or filter for this group of listeners
        :raises ValueError:    if either `manager` or `key_or_filter` is `None`
        """
        if manager is None:
            raise ValueError("Argument `manager` must not be None")
        if key_or_filter is None:
            raise ValueError("Argument `key_or_filter` must not be None")

        super().__init__(manager, key_or_filter)

    # noinspection PyProtectedMember
    def _post_subscribe(self, request: MapListenerRequest) -> None:
        manager: _MapEventsManagerV1[K, V] = self._manager
        key: K = manager._serializer.deserialize(request.key)
        self._manager._key_group_subscribed(key, self)

    # noinspection PyProtectedMember
    def _post_unsubscribe(self, request: MapListenerRequest) -> None:
        manager: _MapEventsManager[K, V] = self._manager
        key: K = manager._serializer.deserialize(request.key)
        manager._key_group_unsubscribed(key)


class _FilterListenerGroupV0(_ListenerGroupV0[K, V]):
    """A ListenerGroup for Filter-based MapListeners"""

    def __init__(self, manager: _MapEventsManagerV0[K, V], filter: Filter) -> None:
        """
        Creates a new _FilterListenerGroupV0
        :param manager:  the _MapEventManager
        :param filter:   the group Filter
        """
        super().__init__(manager, filter)

    # noinspection PyProtectedMember
    def _post_subscribe(self, request: MapListenerRequest) -> None:
        self._manager._filter_group_subscribed(request.filterId, cast(Filter, self._key_or_filter), self)

    # noinspection PyProtectedMember
    def _post_unsubscribe(self, request: MapListenerRequest) -> None:
        self._manager._filter_group_unsubscribed(request.filterId, cast(Filter, self._key_or_filter))


class _FilterListenerGroupV1(_ListenerGroupV1[K, V]):
    """A ListenerGroup for Filter-based MapListeners"""

    def __init__(self, manager: _MapEventsManagerV1[K, V], filter: Filter) -> None:
        """
        Creates a new _KeyListenerGroup
        :param manager:  the _MapEventManager
        :param filter:   the group Filter
        """
        super().__init__(manager, filter)

    # noinspection PyProtectedMember
    def _post_subscribe(self, request: MapListenerRequest) -> None:
        self._manager._filter_group_subscribed(self._filter_id, cast(Filter, self._key_or_filter), self)

    # noinspection PyProtectedMember
    def _post_unsubscribe(self, request: MapListenerRequest) -> None:
        self._manager._filter_group_unsubscribed(self._filter_id, cast(Filter, self._key_or_filter))


class _MapEventsManager(Generic[K, V], ABC):
    """MapEventsManager handles registration, de-registration of callbacks, and
    notification of {@link MapEvent}s to callbacks. Since multiple callbacks can
    be registered for a single key / filter, this class relies on another internal
    class called ListenerGroup which maintains the collection of callbacks.

    There are two maps that are maintained:

    1. A Map of string keys mapped to a ListenerGroup, which is used to identify
       thd group of callbacks for a single key.
    2. A Map of filter => ListenerGroup that is used to identify the group of callbacks
       for a MapEventFilter.

    When a filter is subscribed, the server responds with a unique filterID.This filterID
    is what is specified is a MapEvent. So, this class maintains a third Map of
    filterID to ListenerGroup for efficiently identifying the ListenerGroup for a filterID.
    """

    _DEFAULT_FILTER: MapEventFilter[K, V] = MapEventFilter.from_filter(Filters.always())
    """The default filter to use if none is specified."""

    _named_map: coherence.client.NamedMap[K, V]
    """the NamedMap that is to be the source of the events."""

    _client: NamedCacheServiceStub
    """the gRPC cache client."""

    _serializer: Serializer
    """the Serializer to applied to in and outbound payloads."""

    _emitter: EventEmitter
    """the EventEmitter that will be used to emit MapEvents."""

    _map_name: str
    """The logical name of the provided NamedMap."""

    _key_map: dict[K, _ListenerGroup[K, V, Any]]
    """Contains mappings between a key and its group of MapListeners."""

    _filter_map: dict[Filter, _ListenerGroup[K, V, Any]]
    """Contains mappings between a Filter and its group of MapListeners."""

    _filter_id_listener_group_map: dict[int, _ListenerGroup[K, V, Any]]
    """Contains mappings between a logical filter ID and its ListenerGroup."""

    _event_stream: Optional[grpc.aio.StreamStreamCall]
    """gRPC bidirectional stream for subscribing/unsubscribing MapListeners and receiving MapEvents from
       the proxy."""

    _open: bool
    """"Flag indicating the event stream is open and ready for listener registrations and
    incoming events."""

    _pending_registrations: dict[str | int, _ListenerGroup[K, V, Any]]
    """The mapping of pending listener registrations keyed by request uid."""

    _background_tasks: Set[Task[None]]

    def __init__(
        self,
        named_map: coherence.client.NamedMap[K, V],
        session: coherence.Session,
        serializer: Serializer,
        emitter: EventEmitter,
    ) -> None:
        """
        Constructs a new _MapEventManager.
        :param named_map:   the 'source' of the events
        :param session:     the Session associated with this NamedMap
        :param serializer:  the Serializer that will be used for ser/deser operations
        :param emitter:     the internal event emitter used to notify registered MapListeners
        """
        self._named_map = named_map
        self._serializer = serializer
        self._emitter = emitter
        self._map_name = named_map.name
        self._session = session

        self._key_map = {}
        self._filter_map = {}
        self._filter_id_listener_group_map = {}
        self._pending_registrations = {}

        self._event_stream = None
        self._open = False
        self._background_tasks = set()
        self._stream_waiter = Event()

        session.on(SessionLifecycleEvent.DISCONNECTED, self._close)

        # intentionally ignoring the typing here to avoid complicating the
        # callback API exposed on the session
        # noinspection PyTypeChecker
        session.on(SessionLifecycleEvent.RECONNECTED, self._reconnect)

    @abstractmethod
    def _close(self) -> None:
        pass

    @abstractmethod
    async def _reconnect(self) -> None:
        pass

    @abstractmethod
    def _new_key_group(self, key: K) -> _ListenerGroup[K, V, Any]:
        pass

    @abstractmethod
    def _new_filter_group(self, filter: Filter) -> _ListenerGroup[K, V, Any]:
        pass

    async def _register_key_listener(self, listener: MapListener[K, V], key: K, lite: bool = False) -> None:
        """
        Registers the specified listener to listen for events matching the provided key.
        :param listener:  the MapListener to register
        :param key:       the key to listener to
        :param lite:      `True` if the event should only include the key, or `False`
                          if the event should include old and new values as well as the key
        """
        group: Optional[_ListenerGroup[K, V, Any]] = self._key_map.get(key, None)

        if group is None:
            group = self._new_key_group(key)
            self._key_map[key] = group

        await group.add_listener(listener, lite)

    async def _remove_key_listener(self, listener: MapListener[K, V], key: K) -> None:
        """
        Removes the registration of the listener for the provided key.
        :param listener:  the MapListener to remove
        :param key:       they key the listener was associated with
        """
        group: Optional[_ListenerGroup[K, V, Any]] = self._key_map.get(key, None)

        if group is not None:
            await group.remove_listener(listener)

    async def _register_filter_listener(
        self, listener: MapListener[K, V], filter: Optional[Filter], lite: bool = False
    ) -> None:
        """
        Registers the specified listener to listen for events matching the provided filter.
        :param listener:  the MapListener to register
        :param filter:    the Filter associated with the listener
        :param lite:      `True` if the event should only include the key, or `False`
          if the event should include old and new values as well as the key
        """
        filter_local: Filter = filter if filter is not None else self._DEFAULT_FILTER
        group: Optional[_ListenerGroup[K, V, Any]] = self._filter_map.get(filter_local, None)

        if group is None:
            group = self._new_filter_group(filter_local)
            self._filter_map[filter_local] = group
        await group.add_listener(listener, lite)

    async def _remove_filter_listener(self, listener: MapListener[K, V], filter: Optional[Filter]) -> None:
        """
        Removes the registration of the listener for the provided filter.
        :param listener:  the MapListener to remove
        :param filter:    the Filter that was used with the listener registration
        """
        filter_local: Filter = filter if filter is not None else self._DEFAULT_FILTER
        group: Optional[_ListenerGroup[K, V, Any]] = self._filter_map.get(filter_local, None)

        if group is not None:
            await group.remove_listener(listener)

    def _key_group_subscribed(self, key: K, group: _ListenerGroup[K, V, Any]) -> None:
        """
        Called internally by _KeyListenerGroup when a key listener is subscribed.
        :param key:    the registration key
        :param group:  the registered group
        """
        self._key_map[key] = group

    def _key_group_unsubscribed(self, key: K) -> None:
        """
        Called internally by _KeyListenerGroup when a listener is unsubscribed.
        :param key:  the key used at registration
        """
        del self._key_map[key]

    def _filter_group_subscribed(self, filter_id: int, filter: Filter, group: _ListenerGroup[K, V, Any]) -> None:
        """
        Called internally by _FilterListenerGroup when a filter listener is subscribed.
        :param filter_id:  the ID of the filter
        :param filter:     the Filter associated with the listener registration
        :param group:      the registered group
        """
        self._filter_id_listener_group_map[filter_id] = group
        self._filter_map[filter] = group

    def _filter_group_unsubscribed(self, filter_id: int, filter: Filter) -> None:
        """
        Called internally by _FilterListenerGroup when a filter listener is unsubscribed.
        :param filter_id:  the ID of the filter
        :param filter:     the Filter used at registration
        """
        del self._filter_id_listener_group_map[filter_id]
        del self._filter_map[filter]


class _MapEventsManagerV0(_MapEventsManager[K, V]):
    """MapEventsManager implementation for V0 of the gRPC proxy."""

    # noinspection PyProtectedMember
    def __init__(
        self,
        named_map: coherence.client.NamedMap[K, V],
        session: coherence.Session,
        client: NamedCacheServiceStub,
        serializer: Serializer,
        emitter: EventEmitter,
    ) -> None:
        """
        Constructs a new _MapEventManager.
        :param named_map:   the 'source' of the events
        :param session:     the Session associated with this NamedMap
        :param client:      the gRPC client
        :param serializer:  the Serializer that will be used for ser/deser operations
        :param emitter:     the internal event emitter used to notify registered MapListeners
        """
        super().__init__(named_map, session, serializer, emitter)
        self._client = client
        self._request_factory = RequestFactory(self._map_name, session.scope, serializer)

    def _new_key_group(self, key: K) -> _ListenerGroup[K, V, Any]:
        return _KeyListenerGroupV0(self, key)

    def _new_filter_group(self, filter: Filter) -> _ListenerGroup[K, V, Any]:
        return _FilterListenerGroupV0(self, filter)

    def _close(self) -> None:
        """Close the gRPC event stream and any background tasks."""

        event_stream: grpc.aio.StreamStreamCall = self._event_stream
        if event_stream is not None:
            event_stream.cancel()
            self._event_stream = None

        self._open = False
        for task in self._background_tasks:
            task.cancel()
        self._background_tasks.clear()

    # noinspection PyProtectedMember
    async def _reconnect(self) -> None:
        group: _ListenerGroup[K, V, Any]
        for group in self._key_map.values():
            await group._subscribe(group._registered_lite)

        for group in self._filter_map.values():
            await group._subscribe(group._registered_lite)

    async def _ensure_stream(self) -> grpc.aio.StreamStreamCall:
        """
        Initialize the event stream for MapListener events.
        """
        if self._event_stream is None:
            event_stream: grpc.aio.StreamStreamCall = self._client.events()
            await event_stream.write(self._request_factory.map_event_subscribe())
            self._event_stream = event_stream
            read_task: Task[None] = asyncio.create_task(self._handle_response())
            self._background_tasks.add(read_task)
            # we use asyncio.timeout here instead of using the gRPC timeout
            # as any deadline set on the stream will result in a loss of events
            try:
                await asyncio.wait_for(self._stream_waiter.wait(), self._session.options.request_timeout_seconds)
            except TimeoutError:
                s = (
                    "Deadline [{0} seconds] exceeded waiting for event stream"
                    " to become ready. Server address - {1})".format(
                        str(self._session.options.request_timeout_seconds), self._session.options.address
                    )
                )
                raise TimeoutError(s)

        return self._event_stream

    # noinspection PyProtectedMember
    async def _handle_response(self) -> None:
        """
        Handles reading data from the event stream and invoking the appropriate logic
        for various MapListenerResponse messages that may be sent by the backend.
        """
        if not self._open:  # will be triggered on first response
            event_stream: grpc.aio.StreamStreamCall = await self._ensure_stream()
            await event_stream.read()
            self._open = True
            self._stream_waiter.set()  # notify any callers waiting for stream init
            self._stream_waiter.clear()
            try:
                while self._open:
                    await asyncio.sleep(0.1)
                    response: MapListenerResponse = await event_stream.read()
                    if response.HasField("subscribed"):
                        subscribed = response.subscribed
                        group: Optional[_ListenerGroup[K, V, Any]] = self._pending_registrations.get(
                            subscribed.uid, None
                        )
                        if group is not None:
                            group._subscribe_complete()
                    elif response.HasField("destroyed"):
                        destroyed_cache: str = response.destroyed.cache
                        if destroyed_cache == self._map_name:
                            self._emitter.emit(MapLifecycleEvent.DESTROYED.value, self._map_name)
                    elif response.HasField("truncated"):
                        truncated_cache: str = response.truncated.cache
                        if truncated_cache == self._map_name:
                            self._emitter.emit(MapLifecycleEvent.TRUNCATED.value, self._map_name)
                    elif response.HasField("event"):
                        response_event = response.event
                        event: MapEvent[K, V] = MapEvent(self._named_map, response_event, self._serializer)
                        for _id in response_event.filterIds:
                            filter_group: Optional[_ListenerGroup[K, V, Any]] = self._filter_id_listener_group_map.get(
                                _id, None
                            )
                            if filter_group is not None:
                                filter_group._notify_listeners(event)

                        key_group = self._key_map.get(event.key, None)
                        if key_group is not None:
                            key_group._notify_listeners(event)
            except asyncio.CancelledError:
                return


class _MapEventsManagerV1(_MapEventsManager[K, V]):
    def __init__(
        self,
        named_map: coherence.client.NamedMap[K, V],
        session: coherence.Session,
        serializer: Serializer,
        emitter: EventEmitter,
        request_factory: RequestFactoryV1,
    ) -> None:
        super().__init__(named_map, session, serializer, emitter)
        self.request_factory = request_factory
        print(self)

    @property
    def request_factory(self) -> RequestFactoryV1:
        return self._request_factory

    @request_factory.setter
    def request_factory(self, value: RequestFactoryV1) -> None:
        self._request_factory = value

    async def _ensure_stream(self) -> grpc.aio.StreamStreamCall:
        pass  # in v1, this is a no-op

    def _new_key_group(self, key: K) -> _ListenerGroup[K, V, Any]:
        return _KeyListenerGroupV1(self, key)

    def _new_filter_group(self, filter: Filter) -> _ListenerGroup[K, V, Any]:
        return _FilterListenerGroupV1(self, filter)

    def _close(self) -> None:
        pass

    async def _reconnect(self) -> None:
        pass
