# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

import abc
import asyncio
import logging
import os
import sys
import textwrap
import time
import traceback
import uuid
from asyncio import Condition, Event, Task
from contextlib import asynccontextmanager
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Final,
    Generic,
    Literal,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypeVar,
    cast,
    no_type_check,
)

# noinspection PyPackageRequirements
import grpc
from google.protobuf.json_format import MessageToJson
from grpc.aio import Channel, StreamStreamMultiCallable
from pymitter import EventEmitter

from .aggregator import AverageAggregator, EntryAggregator, PriorityAggregator, SumAggregator
from .cache_service_messages_v1_pb2 import MapEventMessage, NamedCacheResponse, ResponseType
from .comparator import Comparator
from .entry import MapEntry
from .event import (
    MapEvent,
    MapEventType,
    MapLifecycleEvent,
    MapListener,
    SessionLifecycleEvent,
    _ListenerGroup,
    _MapEventsManagerV0,
    _MapEventsManagerV1,
)
from .extractor import ValueExtractor
from .filter import Filter
from .local_cache import CacheStats, LocalCache, NearCacheOptions
from .messages_pb2 import PageRequest
from .nslookup import AsyncNSLookup
from .processor import EntryProcessor
from .proxy_service_messages_v1_pb2 import ProxyRequest, ProxyResponse
from .proxy_service_v1_pb2_grpc import ProxyServiceStub
from .serialization import Serializer, SerializerRegistry
from .services_pb2_grpc import NamedCacheServiceStub
from .util import (
    Dispatcher,
    PagingDispatcher,
    RequestFactory,
    RequestFactoryV1,
    ResponseObserver,
    StreamingDispatcher,
    UnaryDispatcher,
    cur_time_millis,
)

_SPECIFY_EXTRACTOR: Final[str] = "A ValueExtractor must be specified"
_SPECIFY_MAP_LISTENER: Final[str] = "A MapListener must be specified"

E = TypeVar("E")
K = TypeVar("K")
V = TypeVar("V")
R = TypeVar("R")
T = TypeVar("T")

COH_LOG = logging.getLogger("coherence")


@asynccontextmanager
async def request_timeout(seconds: float):  # type: ignore
    from . import _TIMEOUT_CONTEXT_VAR

    request_timeout = _TIMEOUT_CONTEXT_VAR.set(seconds)
    try:
        yield
    finally:
        _TIMEOUT_CONTEXT_VAR.reset(request_timeout)


# noinspection PyUnresolvedReferences,PyProtectedMember
class _Handshake:
    def __init__(self, session: Session):
        self._protocol_version: int = 0
        self._proxy_version: str = "unknown"
        self._proxy_member_id: int = 0
        self._session = session
        self._channel: Channel = session.channel
        self._stream: Optional[StreamStreamMultiCallable] = None

    async def handshake(self) -> None:
        stub: ProxyServiceStub = ProxyServiceStub(self._channel)
        stream: StreamStreamMultiCallable = stub.subChannel()
        try:
            await stream.write(RequestFactoryV1.init_sub_channel())
            response = await asyncio.wait_for(stream.read(), self._session.options.request_timeout_seconds)
            stream.cancel()  # cancel the stream; no longer needed
            self._proxy_version = response.init.version
            self._protocol_version = response.init.protocolVersion
            self._proxy_member_id = response.init.proxyMemberId
        except grpc.aio._call.AioRpcError as e:
            error_code: int = e.code().value[0]
            if (
                # Check for StatusCode INTERNAL as work around for
                # grpc issue https://github.com/grpc/grpc/issues/36066
                error_code == grpc.StatusCode.UNIMPLEMENTED.value[0]
                or error_code == grpc.StatusCode.INTERNAL.value[0]
            ):
                return
            else:
                raise RuntimeError(
                    f"Unexpected error, {e}, when attempting to handshake with proxy: {e.details()}"
                ) from e
        except asyncio.TimeoutError as e:
            raise RuntimeError("Handshake with proxy timed out") from e
        finally:
            stream.cancel()

    @property
    def protocol_version(self) -> int:
        return self._protocol_version

    @property
    def proxy_version(self) -> str:
        return self._proxy_version

    @property
    def proxy_member_id(self) -> int:
        return self._proxy_member_id


@no_type_check
def _pre_call_cache(func):
    def inner(self, *args, **kwargs):
        if not self.active:
            raise RuntimeError("Cache [] has been " + "released" if self.released else "destroyed")

        return func(self, *args, **kwargs)

    async def inner_async(self, *args, **kwargs):
        if not self.active:
            raise RuntimeError(
                "Cache [{}] has been {}.".format(self.name, "released" if self.released else "destroyed")
            )

        # noinspection PyProtectedMember
        await self._session._wait_for_ready()

        return await func(self, *args, **kwargs)

    if asyncio.iscoroutinefunction(func):
        return inner_async
    return inner


@no_type_check
def _pre_call_session(func):
    def inner(self, *args, **kwargs):
        if self._closed:
            raise RuntimeError("Session has been closed.")

        return func(self, *args, **kwargs)

    async def inner_async(self, *args, **kwargs):
        if self._closed:
            raise RuntimeError("Session has been closed.")

        return await func(self, *args, **kwargs)

    if asyncio.iscoroutinefunction(func):
        return inner_async
    return inner


class CacheOptions:
    def __init__(self, default_expiry: int = 0, near_cache_options: Optional[NearCacheOptions] = None):
        """
        Constructs a new CacheOptions which may be used in configuring the behavior of a NamedMap or NamedCache.

        :param default_expiry: the default expiration time, in millis, that will be applied to entries
         inserted into a NamedMap or NamedCache
        :param near_cache_options: the near caching configuration this NamedMap or NamedCache should use
        """
        super().__init__()
        self._default_expiry: int = default_expiry if default_expiry >= 0 else -1
        self._near_cache_options = near_cache_options

    def __str__(self) -> str:
        """
        :return: the string representation of this CacheOptions instance.
        """
        result: str = f"CacheOptions(default-expiry={self._default_expiry}"
        result += ")" if self.near_cache_options is None else f", near-cache-options={self.near_cache_options})"
        return result

    def __eq__(self, other: Any) -> bool:
        """
        Compare two CacheOptions for equality.

        :param other: the CacheOptions to compare against
        :return: True if equal otherwise False
        """
        if self is other:
            return True

        if isinstance(other, CacheOptions):
            return (
                self.default_expiry == other.default_expiry and True
                if self.near_cache_options is None
                else self.near_cache_options == other.near_cache_options
            )

        return False

    @property
    def default_expiry(self) -> int:
        """
        The configured default entry time-to-live.

        :return: the default entry ttl
        """
        return self._default_expiry

    @property
    def near_cache_options(self) -> Optional[NearCacheOptions]:
        """
        The configured NearCacheOptions.

        :return: the configured NearCacheOptions, if any
        """
        return self._near_cache_options


class NamedMap(abc.ABC, Generic[K, V]):
    # noinspection PyUnresolvedReferences
    """
    A Map-based data-structure that manages entries across one or more processes. Entries are typically managed in
    memory, and are often comprised of data that is also stored persistently, on disk.

    :param K:  the type of the map entry keys
    :param V:  the type of the map entry values
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Returns the logical name of this NamedMap"""

    @property
    @abc.abstractmethod
    def session(self) -> Session:
        """Returns the Session associated with this NamedMap"""

    @property
    @abc.abstractmethod
    def options(self) -> Optional[CacheOptions]:
        """Returns the CacheOptions associated with this NamedMap"""

    @property
    def near_cache_stats(self) -> Optional[CacheStats]:
        """
        Returns the CacheStats of the near cache, if one has been configured.
        """
        return None

    @abc.abstractmethod
    def on(self, event: MapLifecycleEvent, callback: Callable[[str], None]) -> None:
        """
        Add a callback that will be invoked when the specified MapLifecycleEvent is raised.
        :param event:     the MapLifecycleEvent to listen for
        :param callback:  the callback that will be invoked when the event occurs
        """

    @property
    @abc.abstractmethod
    def destroyed(self) -> bool:
        pass

    @property
    @abc.abstractmethod
    def released(self) -> bool:
        pass

    @property
    def active(self) -> bool:
        return not self.released and not self.destroyed

    @abc.abstractmethod
    async def add_map_listener(
        self, listener: MapListener[K, V], listener_for: Optional[K | Filter] = None, lite: bool = False
    ) -> None:
        """
        Add a MapListener that will receive events (inserts, updates, deletes) that occur
        against the map, with the key, old-value and new-value included.

        :param listener:      the MapListener to register
        :param listener_for:  the optional key that identifies the entry for which to raise events or a Filter
         that will be passed MapEvent objects to select from; a MapEvent will be delivered to the listener only if the
         filter evaluates to `True` for that MapEvent. `None` is equivalent to a Filter that always returns `True`
        :param lite:          optionally pass `True` to indicate that the MapEvent objects do not have to include the
         old or new values in order to allow optimizations
        :raises ValueError: if `listener` is `None`
        """

    @abc.abstractmethod
    async def remove_map_listener(self, listener: MapListener[K, V], listener_for: Optional[K | Filter] = None) -> None:
        """
        Remove a standard map listener that previously registered to receive events.
        :param listener:      the MapListener to be removed
        :param listener_for:  the key or filter, if any, passed to a previous addMapListener invocation
        :raises ValueError: if `listener` is `None`
        """

    @abc.abstractmethod
    async def get(self, key: K) -> Optional[V]:
        """
        Returns the value to which this cache maps the specified key.

        :param key: the key whose associated value is to be returned

        :Example:

         >>> import asyncio
         >>> from typing import Any, AsyncGenerator, Optional, TypeVar
         >>> from coherence import NamedCache, Session
         >>> K = TypeVar("K")
         >>> V = TypeVar("V")
         >>> R = TypeVar("R")
         >>> session: Session = Session(None)
         >>> cache: NamedCache[Any, Any] = await session.get_cache("test")
         >>> k: str = "one"
         >>> v: str = "only-one"
         >>> await cache.put(k, v)
         >>> r = await cache.get(k)
         >>> print(r)
         only-one

        """

    @abc.abstractmethod
    async def get_or_default(self, key: K, default_value: Optional[V] = None) -> Optional[V]:
        """
        Returns the value to which the specified key is mapped, or the specified `defaultValue`
        if this map contains no mapping for the key.

        :param key: the key whose associated value is to be returned
        :param default_value: defaultValue if this map contains no mapping for the key.
        :return: value for the key in the map or the `defaultValue`
        """

    @abc.abstractmethod
    async def get_all(self, keys: set[K]) -> AsyncIterator[MapEntry[K, V]]:
        """
        Get all the specified keys if they are in the map. For each key that is in the map,
        that key and its corresponding value will be placed in the map that is returned by
        this method. The absence of a key in the returned map indicates that it was not in the cache,
        which may imply (for caches that can load behind the scenes) that the requested data
        could not be loaded.

        :param keys: an Iterable of keys that may be in this map
        :return: an AsyncIterator of MapEntry instances for the specified keys passed in `keys`
        """

    @abc.abstractmethod
    async def put(self, key: K, value: V) -> Optional[V]:
        """
        Associates the specified value with the specified key in this map. If the
        map previously contained a mapping for this key, the old value is replaced.

        :param key: the key with which the specified value is to be associated
        :param value: the value to be associated with the specified key
        :return: the previous value associated with the specified key, or `None`
         if there was no mapping for key. A `None` return can also indicate
         that the map previously associated `None` with the specified key
         if the implementation supports `None` values
        """

    @abc.abstractmethod
    async def put_if_absent(self, key: K, value: V) -> Optional[V]:
        """
        If the specified key is not already associated with a value (or is mapped to `None`) associates
        it with the given value and returns `None`, else returns the current value.

        :param key: the key with which the specified value is to be associated
        :param value: the value to be associated with the specified key
        :return: the previous value associated with the specified key, or `None` if there was no mapping for key. A
         `None` return can also indicate that the map previously associated `None` with the specified key
         if the implementation supports `None` values

        """

    @abc.abstractmethod
    async def put_all(self, map: dict[K, V], ttl: Optional[int] = None) -> None:
        """
        Copies all mappings from the specified map to this map

        :param map: the map to copy from
        :param ttl: the time to live for the map entries
        """

    @abc.abstractmethod
    async def clear(self) -> None:
        """
        Clears all the mappings in the 'NamedMap'.

        """

    @abc.abstractmethod
    async def destroy(self) -> None:
        """
        Release and destroy this cache.

        Warning: This method is used to completely destroy the specified cache
        across the cluster. All references in the entire cluster to this cache
        will be invalidated, the cached data will be cleared, and all resources
        will be released.
        """

    @abc.abstractmethod
    async def release(self) -> None:
        """
        Release local resources associated with instance.

        """

    @abc.abstractmethod
    async def truncate(self) -> None:
        """
        Truncates the cache.  Unlike :func:`coherence.client.NamedMap.clear()`, this function does not generate an
        event for each removed entry.

        """

    @abc.abstractmethod
    async def remove(self, key: K) -> Optional[V]:
        """
        Removes the mapping for a key from this map if it is present.

        :param key: key whose mapping is to be removed from the map
        :return: the previous value associated with key, or `None` if there was no mapping for key
        """

    @abc.abstractmethod
    async def remove_mapping(self, key: K, value: V) -> bool:
        """
        Removes the entry for the specified key only if it is currently mapped to the specified value.

        :param key: key with which the specified value is associated
        :param value: expected to be associated with the specified key
        :return: resolving to true if the value was removed
        """

    @abc.abstractmethod
    async def replace(self, key: K, value: V) -> Optional[V]:
        """
        Replaces the entry for the specified key only if currently mapped to the specified value.

        :param key: key whose associated value is to be replaced
        :param value: value expected to be associated with the specified key
        :return: resolving to the previous value associated with the specified key, or `None` if there was no mapping
         for the key. (A `None` return can also indicate that the map previously associated `None` with the key
         if the implementation supports `None` values.)
        """

    @abc.abstractmethod
    async def replace_mapping(self, key: K, old_value: V, new_value: V) -> bool:
        """
        Replaces the entry for the specified key only if currently mapped to the specified value.

        :param key:         key whose associated value is to be removed
        :param old_value:   value expected to be associated with the specified key
        :param new_value:   value to be associated with the specified key
        :return: resolving to `true` if the value was replaced
        """

    @abc.abstractmethod
    async def contains_key(self, key: K) -> bool:
        """
        Returns `true` if the specified key is mapped a value within the cache.

        :param key: the key whose presence in this cache is to be tested
        :return: resolving to `true` if the key is mapped to a value, or `false` if it does not
        """

    @abc.abstractmethod
    async def contains_value(self, value: V) -> bool:
        """
        Returns `true` if the specified value is mapped to some key.

        :param value: the value expected to be associated with some key
        :return: resolving to `true` if a mapping exists, or `false` if it does not
        """

    @abc.abstractmethod
    async def is_empty(self) -> bool:
        """
        Returns `true` if this map contains no key-value mappings.

        :return: `true` if this map contains no key-value mappings.
        """

    @abc.abstractmethod
    async def size(self) -> int:
        """
        Signifies the number of key-value mappings in this map.

        :return: the number of key-value mappings in this map
        """

    @abc.abstractmethod
    async def invoke(self, key: K, processor: EntryProcessor[R]) -> Optional[R]:
        """
        Invoke the passed EntryProcessor against the Entry specified by the
        passed key, returning the result of the invocation.

        :param key: the key to process - it is not required to exist within the Map
        :param processor: the EntryProcessor to use to process the specified key
        :return: the result of the invocation as returned from the EntryProcessor
        """

    @abc.abstractmethod
    async def invoke_all(
        self, processor: EntryProcessor[R], keys: Optional[set[K]] = None, filter: Optional[Filter] = None
    ) -> AsyncIterator[MapEntry[K, R]]:
        """
        Invoke the passed EntryProcessor against the set of entries that are selected by the given Filter,
        returning the result of the invocation for each.

        Unless specified otherwise, implementations will perform this operation in two steps:
            1. use the filter to retrieve a matching entry set
            2. apply the agent to every filtered entry.

        This algorithm assumes that the agent's processing does not affect the result of the specified filter
        evaluation, since the filtering and processing could be performed in parallel on different threads. If this
        assumption does not hold, the processor logic has to be idempotent, or at least re-evaluate the filter. This
        could be easily accomplished by wrapping the processor with the ConditionalProcessor.

        :param processor: the EntryProcessor to use to process the specified keys
        :param keys: the keys to process these keys are not required to exist within the Map
        :param filter: a Filter that results in the set of keys to be processed
        :return: an AsyncIterator of MapEntry instances containing the results of invoking the EntryProcessor against
         each of the specified keys
        """

    @abc.abstractmethod
    async def aggregate(
        self, aggregator: EntryAggregator[R], keys: Optional[set[K]] = None, filter: Optional[Filter] = None
    ) -> Optional[R]:
        """
        Perform an aggregating operation against the entries specified by the passed keys.

        :param aggregator: the EntryAggregator that is used to aggregate across the specified entries of this Map
        :param keys: the Iterable of keys that specify the entries within this Map to aggregate across
        :param filter: the Filter that is used to select entries within this Map to aggregate across
        :return: the result of the invocation as returned from the EntryProcessor
        """

    @abc.abstractmethod
    async def values(
        self, filter: Optional[Filter] = None, comparator: Optional[Comparator] = None, by_page: bool = False
    ) -> AsyncIterator[V]:
        """
        Return a Set of the values contained in this map that satisfy the criteria expressed by the filter.
        If no filter or comparator is specified, it returns a Set view of the values contained in this map.The
        collection is backed by the map, so changes to the map are reflected in the collection, and vice versa. If
        the map is modified while an iteration over the collection is in progress (except through the iterator's own
        `remove` operation), the results of the iteration are undefined.

        :param filter: the Filter object representing the criteria that the entries of this map should satisfy
        :param comparator:  the Comparator object which imposes an ordering on entries in the resulting set; or null
         if the entries' natural ordering should be used
        :param by_page: returns the keys in pages (transparently to the caller).  This option is only valid
         if no filter or comparator is provided.
        :return: an AsyncIterator of MapEntry instances resolving to the values that satisfy the specified criteria
        """

    @abc.abstractmethod
    async def keys(self, filter: Optional[Filter] = None, by_page: bool = False) -> AsyncIterator[K]:
        """
        Return a set view of the keys contained in this map for entries that satisfy the criteria expressed by the
        filter.

        :param filter: the Filter object representing the criteria that the entries of this map should satisfy
        :param by_page: returns the keys in pages (transparently to the caller).  This option is only valid
         if no filter is provided.
        :return: an AsyncIterator of keys for entries that satisfy the specified criteria
        """

    @abc.abstractmethod
    async def entries(
        self, filter: Optional[Filter] = None, comparator: Optional[Comparator] = None, by_page: bool = False
    ) -> AsyncIterator[MapEntry[K, V]]:
        """
        Return a set view of the entries contained in this map that satisfy the criteria expressed by the filter.
        Each element in the returned set is a :class:`coherence.client.MapEntry`.

        :param filter: the Filter object representing the criteria that the entries of this map should satisfy
        :param comparator: the Comparator object which imposes an ordering on entries in the resulting set; or `None`
         if the entries' values natural ordering should be used
        :param by_page: returns the keys in pages (transparently to the caller).  This option is only valid
         if no filter or comparator is provided.
        :return: an AsyncIterator of MapEntry instances that satisfy the specified criteria
        """

    @abc.abstractmethod
    def add_index(
        self, extractor: ValueExtractor[T, E], ordered: bool = False, comparator: Optional[Comparator] = None
    ) -> None:
        """
        Add an index to this map.

        :param extractor: The :class:`coherence.extractor.ValueExtractor` object that is used to extract
                   an indexable Object from a value stored in the
                   indexed Map. Must not be 'None'.
        :param ordered: true if the contents of the indexed information
                   should be ordered false otherwise.
        :param comparator: The :class:`coherence.comparator.Comparator` object which imposes an ordering
                   on entries in the indexed map or None if the
                   entries' values natural ordering should be used.
        """

    @abc.abstractmethod
    def remove_index(self, extractor: ValueExtractor[T, E]) -> None:
        """
        Removes an index on this `NamedMap`.

        :param extractor: The :class:`coherence.extractor.ValueExtractor` object that is used to extract
                  an indexable Object from a value stored in the
                  indexed Map. Must not be 'None'.

        """


class NamedCache(NamedMap[K, V]):
    # noinspection PyUnresolvedReferences
    """
    A Map-based data-structure that manages entries across one or more processes. Entries are typically managed in
    memory, and are often comprised of data that is also stored in an external system, for example, a database,
    or data that has been assembled or calculated at some significant cost.  Such entries are referred to as being
    `cached`.

    :param K:  the type of the map entry keys
    :param V:  the type of the map entry values
    """

    @abc.abstractmethod
    async def put(self, key: K, value: V, ttl: Optional[int] = None) -> Optional[V]:
        """
        Associates the specified value with the specified key in this map. If the map previously contained a mapping
        for this key, the old value is replaced.

        :param key: the key with which the specified value is to be associated
        :param value: the value to be associated with the specified key
        :param ttl: the expiry time in millis (optional).  If not specified, it will default to the default
          ttl defined in the cache options provided when the cache was obtained
        :return: resolving to the previous value associated with specified key, or `None` if there was no mapping for
         key. A `None` return can also indicate that the map previously associated `None` with the specified key
         if the implementation supports `None` values

        """

    @abc.abstractmethod
    async def put_if_absent(self, key: K, value: V, ttl: Optional[int] = None) -> Optional[V]:
        """
        If the specified key is not already associated with a value (or is mapped to null) associates it with the
        given value and returns `None`, else returns the current value.

        :param key: the key with which the specified value is to be associated
        :param value: the value to be associated with the specified key
        :param ttl: the expiry time in millis (optional).  If not specified, it will default to the default
          ttl defined in the cache options provided when the cache was obtained.
        :return: resolving to the previous value associated with specified key, or `None` if there was no mapping for
         key. A `None` return can also indicate that the map previously associated `None` with the specified key
         if the implementation supports `None` values

        """


class NamedCacheClient(NamedCache[K, V]):
    def __init__(
        self, cache_name: str, session: Session, serializer: Serializer, cache_options: Optional[CacheOptions] = None
    ) -> None:
        self._cache_name: str = cache_name
        self._serializer: Serializer = serializer
        self._client_stub: NamedCacheServiceStub = NamedCacheServiceStub(session.channel)
        self._request_factory: RequestFactory = RequestFactory(cache_name, session.scope, serializer)
        self._emitter: EventEmitter = EventEmitter()
        self._internal_emitter: EventEmitter = EventEmitter()
        self._destroyed: bool = False
        self._released: bool = False
        self._session: Session = session
        self._cache_options: Optional[CacheOptions] = cache_options
        self._default_expiry: int = cache_options.default_expiry if cache_options is not None else 0

        self._setup_event_handlers()

        self._events_manager: _MapEventsManagerV0[K, V] = _MapEventsManagerV0(
            self, session, self._client_stub, serializer, self._internal_emitter
        )

    @property
    def name(self) -> str:
        return self._cache_name

    @property
    def session(self) -> Session:
        return self._session

    @property
    def destroyed(self) -> bool:
        return self._destroyed

    @property
    def released(self) -> bool:
        return self._released

    @property
    def options(self) -> Optional[CacheOptions]:
        return self._cache_options

    @_pre_call_cache
    def on(self, event: MapLifecycleEvent, callback: Callable[[str], None]) -> None:
        self._emitter.on(str(event.value), callback)

    @_pre_call_cache
    async def get(self, key: K) -> Optional[V]:
        g = self._request_factory.get_request(key)
        v = await self._client_stub.get(g)
        if v.present:
            return self._request_factory.serializer.deserialize(v.value)
        else:
            return None

    @_pre_call_cache
    async def get_or_default(self, key: K, default_value: Optional[V] = None) -> Optional[V]:
        v: Optional[V] = await self.get(key)
        if v is not None:
            return v
        else:
            return default_value

    @_pre_call_cache
    async def get_all(self, keys: set[K]) -> AsyncIterator[MapEntry[K, V]]:
        r = self._request_factory.get_all_request(keys)
        stream = self._client_stub.getAll(r)

        return _Stream(self._request_factory.serializer, stream, _entry_producer)

    @_pre_call_cache
    async def put(self, key: K, value: V, ttl: Optional[int] = None) -> Optional[V]:
        p = self._request_factory.put_request(key, value, ttl if ttl is not None else self._default_expiry)
        v = await self._client_stub.put(p)
        return self._request_factory.serializer.deserialize(v.value)

    @_pre_call_cache
    async def put_if_absent(self, key: K, value: V, ttl: Optional[int] = None) -> Optional[V]:
        p = self._request_factory.put_if_absent_request(key, value, ttl if ttl is not None else self._default_expiry)
        v = await self._client_stub.putIfAbsent(p)
        return self._request_factory.serializer.deserialize(v.value)

    @_pre_call_cache
    async def put_all(self, map: dict[K, V]) -> None:
        p = self._request_factory.put_all_request(map)
        await self._client_stub.putAll(p)

    @_pre_call_cache
    async def clear(self) -> None:
        r = self._request_factory.clear_request()
        await self._client_stub.clear(r)

    async def destroy(self) -> None:
        await self.release()
        self._internal_emitter.once(MapLifecycleEvent.DESTROYED.value)
        self._internal_emitter.emit(MapLifecycleEvent.DESTROYED.value, self.name)
        r = self._request_factory.destroy_request()
        await self._client_stub.destroy(r)

    async def release(self) -> None:
        if self.active:
            self._internal_emitter.once(MapLifecycleEvent.RELEASED.value)
            self._internal_emitter.emit(MapLifecycleEvent.RELEASED.value, self.name)

    @_pre_call_cache
    async def truncate(self) -> None:
        self._internal_emitter.once(MapLifecycleEvent.TRUNCATED.value)
        r = self._request_factory.truncate_request()
        await self._client_stub.truncate(r)

    @_pre_call_cache
    async def remove(self, key: K) -> Optional[V]:
        r = self._request_factory.remove_request(key)
        v = await self._client_stub.remove(r)
        return self._request_factory.serializer.deserialize(v.value)

    @_pre_call_cache
    async def remove_mapping(self, key: K, value: V) -> bool:
        r = self._request_factory.remove_mapping_request(key, value)
        v = await self._client_stub.removeMapping(r)
        return self._request_factory.serializer.deserialize(v.value)

    @_pre_call_cache
    async def replace(self, key: K, value: V) -> Optional[V]:
        r = self._request_factory.replace_request(key, value)
        v = await self._client_stub.replace(r)
        return self._request_factory.serializer.deserialize(v.value)

    @_pre_call_cache
    async def replace_mapping(self, key: K, old_value: V, new_value: V) -> bool:
        r = self._request_factory.replace_mapping_request(key, old_value, new_value)
        v = await self._client_stub.replaceMapping(r)
        return self._request_factory.serializer.deserialize(v.value)

    @_pre_call_cache
    async def contains_key(self, key: K) -> bool:
        r = self._request_factory.contains_key_request(key)
        v = await self._client_stub.containsKey(r)
        return self._request_factory.serializer.deserialize(v.value)

    @_pre_call_cache
    async def contains_value(self, value: V) -> bool:
        r = self._request_factory.contains_value_request(value)
        v = await self._client_stub.containsValue(r)
        return self._request_factory.serializer.deserialize(v.value)

    @_pre_call_cache
    async def is_empty(self) -> bool:
        r = self._request_factory.is_empty_request()
        v = await self._client_stub.isEmpty(r)
        return self._request_factory.serializer.deserialize(v.value)

    @_pre_call_cache
    async def size(self) -> int:
        r = self._request_factory.size_request()
        v = await self._client_stub.size(r)
        return self._request_factory.serializer.deserialize(v.value)

    @_pre_call_cache
    async def invoke(self, key: K, processor: EntryProcessor[R]) -> Optional[R]:
        r = self._request_factory.invoke_request(key, processor)
        v = await self._client_stub.invoke(r)
        return self._request_factory.serializer.deserialize(v.value)

    @_pre_call_cache
    async def invoke_all(
        self, processor: EntryProcessor[R], keys: Optional[set[K]] = None, filter: Optional[Filter] = None
    ) -> AsyncIterator[MapEntry[K, R]]:
        r = self._request_factory.invoke_all_request(processor, keys, filter)
        stream = self._client_stub.invokeAll(r)

        return _Stream(self._request_factory.serializer, stream, _entry_producer)

    @_pre_call_cache
    async def aggregate(
        self, aggregator: EntryAggregator[R], keys: Optional[set[K]] = None, filter: Optional[Filter] = None
    ) -> Optional[R]:
        r = self._request_factory.aggregate_request(aggregator, keys, filter)
        results = await self._client_stub.aggregate(r)
        value: Any = self._request_factory.serializer.deserialize(results.value)
        # for compatibility with 22.06
        if isinstance(aggregator, SumAggregator) and isinstance(value, str):
            return cast(R, float(value))
        elif isinstance(aggregator, AverageAggregator) and isinstance(value, str):
            return cast(R, float(value))
        elif isinstance(aggregator, PriorityAggregator):
            # noinspection PyTypeChecker,PyUnresolvedReferences
            pri_agg: PriorityAggregator[R] = aggregator
            if (
                isinstance(pri_agg.aggregator, AverageAggregator) or isinstance(pri_agg.aggregator, SumAggregator)
            ) and isinstance(value, str):
                return cast(R, float(value))
        # end compatibility with 22.06

        return cast(R, value)

    @_pre_call_cache
    async def values(
        self, filter: Optional[Filter] = None, comparator: Optional[Comparator] = None, by_page: bool = False
    ) -> AsyncIterator[V]:
        if by_page and comparator is None and filter is None:
            return _PagedStream(self, _scalar_deserializer)
        else:
            r = self._request_factory.values_request(filter)
            stream = self._client_stub.values(r)

            return _Stream(self._request_factory.serializer, stream, _scalar_producer)

    @_pre_call_cache
    async def keys(self, filter: Optional[Filter] = None, by_page: bool = False) -> AsyncIterator[K]:
        if by_page and filter is None:
            return _PagedStream(self, _scalar_deserializer, True)
        else:
            r = self._request_factory.keys_request(filter)
            stream = self._client_stub.keySet(r)

            return _Stream(self._request_factory.serializer, stream, _scalar_producer)

    @_pre_call_cache
    async def entries(
        self, filter: Optional[Filter] = None, comparator: Optional[Comparator] = None, by_page: bool = False
    ) -> AsyncIterator[MapEntry[K, V]]:
        if by_page and comparator is None and filter is None:
            return _PagedStream(self, _entry_deserializer)
        else:
            r = self._request_factory.entries_request(filter, comparator)
            stream = self._client_stub.entrySet(r)

            return _Stream(self._request_factory.serializer, stream, _entry_producer)

    from .event import MapListener

    # noinspection PyProtectedMember
    @_pre_call_cache
    async def add_map_listener(
        self, listener: MapListener[K, V], listener_for: Optional[K | Filter] = None, lite: bool = False
    ) -> None:
        if listener is None:
            raise ValueError(_SPECIFY_MAP_LISTENER)

        if listener_for is None or isinstance(listener_for, Filter):
            await self._events_manager._register_filter_listener(listener, listener_for, lite)
        else:
            await self._events_manager._register_key_listener(listener, listener_for, lite)

    # noinspection PyProtectedMember
    @_pre_call_cache
    async def remove_map_listener(self, listener: MapListener[K, V], listener_for: Optional[K | Filter] = None) -> None:
        if listener is None:
            raise ValueError(_SPECIFY_MAP_LISTENER)

        if listener_for is None or isinstance(listener_for, Filter):
            await self._events_manager._remove_filter_listener(listener, listener_for)
        else:
            await self._events_manager._remove_key_listener(listener, listener_for)

    @_pre_call_cache
    async def add_index(
        self, extractor: ValueExtractor[T, E], ordered: bool = False, comparator: Optional[Comparator] = None
    ) -> None:
        if extractor is None:
            raise ValueError(_SPECIFY_EXTRACTOR)
        r = self._request_factory.add_index_request(extractor, ordered, comparator)
        await self._client_stub.addIndex(r)

    @_pre_call_cache
    async def remove_index(self, extractor: ValueExtractor[T, E]) -> None:
        if extractor is None:
            raise ValueError(_SPECIFY_EXTRACTOR)
        r = self._request_factory.remove_index_request(extractor)
        await self._client_stub.removeIndex(r)

    def _setup_event_handlers(self) -> None:
        """
        Setup handlers to notify cache-level handlers of events.
        """
        emitter: EventEmitter = self._emitter
        internal_emitter: EventEmitter = self._internal_emitter
        this: NamedCacheClient[K, V] = self
        cache_name = self._cache_name

        # noinspection PyProtectedMember
        def on_destroyed(name: str) -> None:
            if name == cache_name and not this.destroyed:
                this._events_manager._close()
                this._destroyed = True
                emitter.emit(MapLifecycleEvent.DESTROYED.value, name)

        # noinspection PyProtectedMember
        def on_released(name: str) -> None:
            if name == cache_name and not this.released:
                this._events_manager._close()
                this._released = True
                emitter.emit(MapLifecycleEvent.RELEASED.value, name)

        def on_truncated(name: str) -> None:
            if name == cache_name:
                emitter.emit(MapLifecycleEvent.TRUNCATED.value, name)

        internal_emitter.on(MapLifecycleEvent.DESTROYED.value, on_destroyed)
        internal_emitter.on(MapLifecycleEvent.RELEASED.value, on_released)
        internal_emitter.on(MapLifecycleEvent.TRUNCATED.value, on_truncated)

    def __str__(self) -> str:
        return (
            f"NamedCache(name={self.name}, session={self._session.session_id}, serializer={self._serializer},"
            f" released={self.released}, destroyed={self.destroyed})"
        )


class NamedCacheClientV1(NamedCache[K, V]):

    def __init__(
        self, cache_name: str, session: Session, serializer: Serializer, cache_options: Optional[CacheOptions] = None
    ):
        self._cache_name: str = cache_name
        self._cache_id: int = 0
        self._serializer: Serializer = serializer
        self._request_factory: RequestFactoryV1 = RequestFactoryV1(
            cache_name, self._cache_id, session.scope, serializer, lambda: session.options.request_timeout_seconds
        )
        self._emitter: EventEmitter = EventEmitter()
        self._internal_emitter: EventEmitter = EventEmitter()
        self._destroyed: bool = False
        self._released: bool = False
        self._session: Session = session
        self._cache_options: Optional[CacheOptions] = cache_options
        self._default_expiry: int = cache_options.default_expiry if cache_options is not None else 0
        self._near_cache: Optional[LocalCache[K, V]] = None
        self._near_cache_listener: Optional[MapListener[K, V]] = None
        self._near_cache_lock: asyncio.Lock = asyncio.Lock()

        self._events_manager: _MapEventsManagerV1[K, V] = _MapEventsManagerV1(
            self, session, serializer, self._internal_emitter, self._request_factory
        )

        self._stream_handler: StreamHandler = StreamHandler(session, self._request_factory, self._events_manager)
        self._setup_event_handlers()

        near_options: Optional[NearCacheOptions] = None if cache_options is None else cache_options.near_cache_options
        if near_options is not None:
            self._near_cache = LocalCache(cache_name, near_options)

    async def _post_create(self) -> None:
        near: Optional[LocalCache[K, V]] = self._near_cache
        if near is not None:
            # setup event listener
            async def callback(event: MapEvent[K, V]) -> None:
                if event.type == MapEventType.ENTRY_INSERTED or event.type == MapEventType.ENTRY_UPDATED:
                    if await near.contains_key(event.key):
                        val: Optional[V] = event.new
                        if val is not None:
                            await near.put(event.key, val)
                elif event.type == MapEventType.ENTRY_DELETED:
                    # processing a remove
                    await near.remove(event.key)

            self._near_cache_listener = MapListener(synchronous=True).on_any(callback)  # type: ignore
            await self.add_map_listener(self._near_cache_listener)

    def _setup_event_handlers(self) -> None:
        """
        Setup handlers to notify cache-level handlers of events.
        """
        emitter: EventEmitter = self._emitter
        internal_emitter: EventEmitter = self._internal_emitter
        this: NamedCacheClientV1[K, V] = self
        cache_name = self._cache_name

        # noinspection PyProtectedMember
        def on_destroyed(name: str) -> None:
            if name == cache_name and not this.destroyed:
                this._events_manager._close()
                this._destroyed = True
                this._released = True
                emitter.emit(MapLifecycleEvent.DESTROYED.value, name)

        # noinspection PyProtectedMember
        def on_released(name: str) -> None:
            if name == cache_name and not this.released:
                this._events_manager._close()
                this._released = True
                emitter.emit(MapLifecycleEvent.RELEASED.value, name)

        def on_truncated(name: str) -> None:
            if name == cache_name:
                emitter.emit(MapLifecycleEvent.TRUNCATED.value, name)

        internal_emitter.on(MapLifecycleEvent.DESTROYED.value, on_destroyed)
        internal_emitter.on(MapLifecycleEvent.RELEASED.value, on_released)
        internal_emitter.on(MapLifecycleEvent.TRUNCATED.value, on_truncated)

        near: Optional[LocalCache[K, V]] = this._near_cache
        if near is not None:
            # setup lifecycle callbacks to clear the near cache
            async def do_clear() -> None:
                await near.clear()

            self.on(MapLifecycleEvent.TRUNCATED, do_clear)  # type: ignore
            self.on(MapLifecycleEvent.DESTROYED, do_clear)  # type: ignore

    @property
    def cache_id(self) -> int:
        return self._cache_id

    @cache_id.setter
    def cache_id(self, cache_id: int) -> None:
        self._cache_id = cache_id

    @property
    def name(self) -> str:
        return self._cache_name

    @property
    def session(self) -> Session:
        return self._session

    @property
    def options(self) -> Optional[CacheOptions]:
        return self._cache_options

    @property
    def near_cache_stats(self) -> Optional[CacheStats]:
        near_cache: Optional[LocalCache[K, V]] = self._near_cache
        return None if near_cache is None else near_cache.stats

    def on(self, event: MapLifecycleEvent, callback: Callable[[str], None]) -> None:
        self._emitter.on(str(event.value), callback)

    @property
    def destroyed(self) -> bool:
        return self._destroyed

    @property
    def released(self) -> bool:
        return self._released

    async def _ensure_cache(self) -> None:
        dispatcher: UnaryDispatcher[int] = self._request_factory.ensure_request(self._cache_name)
        await dispatcher.dispatch(self._stream_handler)

        self.cache_id = dispatcher.result()
        self._request_factory.cache_id = self.cache_id

    @_pre_call_cache
    async def get(self, key: K) -> Optional[V]:
        near_cache: Optional[LocalCache[K, V]] = self._near_cache

        # check the near cache first
        if near_cache is not None:
            async with self._near_cache_lock:
                result: Optional[V] = await near_cache.get(key)
                if result is not None:
                    return result

                start: int = cur_time_millis()
                dispatcher: UnaryDispatcher[Optional[V]] = self._request_factory.get_request(key)
                await dispatcher.dispatch(self._stream_handler)
                result = dispatcher.result()

                if result is not None:
                    await near_cache.put(key, result)
                    # noinspection PyProtectedMember
                    near_cache.stats._register_misses_millis(cur_time_millis() - start)
        else:
            dispatcher = self._request_factory.get_request(key)
            await dispatcher.dispatch(self._stream_handler)
            result = dispatcher.result()

        return result

    @_pre_call_cache
    async def put(self, key: K, value: V, ttl: Optional[int] = None) -> Optional[V]:
        dispatcher: UnaryDispatcher[Optional[V]] = self._request_factory.put_request(
            key, value, ttl if ttl is not None else self._default_expiry
        )
        await dispatcher.dispatch(self._stream_handler)
        return dispatcher.result()

    @_pre_call_cache
    async def put_if_absent(self, key: K, value: V, ttl: Optional[int] = None) -> Optional[V]:
        dispatcher: UnaryDispatcher[Optional[V]] = self._request_factory.put_if_absent_request(
            key, value, ttl if ttl is not None else self._default_expiry
        )
        await dispatcher.dispatch(self._stream_handler)
        return dispatcher.result()

    # noinspection PyProtectedMember
    @_pre_call_cache
    async def add_map_listener(
        self, listener: MapListener[K, V], listener_for: Optional[K | Filter] = None, lite: bool = False
    ) -> None:
        if listener is None:
            raise ValueError(_SPECIFY_MAP_LISTENER)

        if listener_for is None or isinstance(listener_for, Filter):
            await self._events_manager._register_filter_listener(listener, listener_for, lite)
        else:
            await self._events_manager._register_key_listener(listener, listener_for, lite)

    # noinspection PyProtectedMember
    @_pre_call_cache
    async def remove_map_listener(self, listener: MapListener[K, V], listener_for: Optional[K | Filter] = None) -> None:
        if listener is None:
            raise ValueError(_SPECIFY_MAP_LISTENER)

        if listener_for is None or isinstance(listener_for, Filter):
            await self._events_manager._remove_filter_listener(listener, listener_for)
        else:
            await self._events_manager._remove_key_listener(listener, listener_for)

    @_pre_call_cache
    async def get_or_default(self, key: K, default_value: Optional[V] = None) -> Optional[V]:
        v: Optional[V] = await self.get(key)
        if v is not None:
            return v
        else:
            return default_value

    # noinspection PyProtectedMember
    @_pre_call_cache
    async def get_all(self, keys: set[K]) -> AsyncIterator[MapEntry[K, V]]:
        near_cache: Optional[LocalCache[K, V]] = self._near_cache
        result: dict[K, V]

        # check the near cache first
        if near_cache is not None:
            async with self._near_cache_lock:
                result = await near_cache.get_all(keys)
                if result is not None:
                    if len(result) == len(keys):
                        # all keys were found, return an AsyncIterator
                        # over those results
                        async def async_iter() -> AsyncIterator[MapEntry[K, V]]:
                            for key, value in result.items():
                                yield MapEntry(key, value)

                        return async_iter()
                    else:
                        # some keys are present within the near cache; make
                        # a remote call to obtain the keys that are missing.
                        stats: CacheStats = near_cache.stats
                        remote_keys: set[K] = keys.difference(result)
                        start: int = cur_time_millis()
                        dispatcher: StreamingDispatcher[MapEntry[K, V]] = self._request_factory.get_all_request(
                            remote_keys
                        )
                        await dispatcher.dispatch(self._stream_handler)
                        stats._register_misses_millis(cur_time_millis() - start)

                        # we could return a composite AsyncIterator that would
                        # yield the local keys followed by the results from the
                        # remote call, but doing could result in additional
                        # remote calls if there are concurrent get_all() calls
                        # that start the same time.  Instead, populate the
                        # near cache while locked and then return results
                        # This is not the most memory efficient, but it makes
                        # the stats more likely to make sense to the user.
                        remote_entries: list[MapEntry[K, V]] = []
                        async for entry in dispatcher:
                            await near_cache.put(entry.key, entry.value)
                            remote_entries.append(entry)

                        stats._register_misses_millis(cur_time_millis() - start)

                        # noinspection PyProtectedMember
                        async def async_iter() -> AsyncIterator[MapEntry[K, V]]:
                            for key, value in result.items():
                                yield MapEntry(key, value)
                            for remote_entry in remote_entries:
                                yield remote_entry

                        return async_iter()
                else:
                    dispatcher = self._request_factory.get_all_request(keys)
                    await dispatcher.dispatch(self._stream_handler)
                    return dispatcher
        else:
            dispatcher = self._request_factory.get_all_request(keys)
            await dispatcher.dispatch(self._stream_handler)
            return dispatcher

    @_pre_call_cache
    async def put_all(self, kv_map: dict[K, V], ttl: Optional[int] = 0) -> None:
        dispatcher: Dispatcher = self._request_factory.put_all_request(kv_map, ttl)
        await dispatcher.dispatch(self._stream_handler)

    @_pre_call_cache
    async def clear(self) -> None:
        dispatcher: Dispatcher = self._request_factory.clear_request()
        await dispatcher.dispatch(self._stream_handler)
        if self._near_cache is not None:
            await self._near_cache.clear()

    async def destroy(self) -> None:
        self._internal_emitter.once(MapLifecycleEvent.DESTROYED.value)
        self._internal_emitter.emit(MapLifecycleEvent.DESTROYED.value, self.name)
        dispatcher: Dispatcher = self._request_factory.destroy_request()
        await dispatcher.dispatch(self._stream_handler)

    async def release(self) -> None:
        if self.active:
            await self._stream_handler.close()
            self._internal_emitter.once(MapLifecycleEvent.RELEASED.value)
            self._internal_emitter.emit(MapLifecycleEvent.RELEASED.value, self.name)

            if self._near_cache is not None:
                await self._near_cache.release()

    @_pre_call_cache
    async def truncate(self) -> None:
        dispatcher: Dispatcher = self._request_factory.truncate_request()
        await dispatcher.dispatch(self._stream_handler)

        # clear the near cache as the lifecycle listeners are not synchronous
        if self._near_cache is not None:
            await self._near_cache.clear()

    @_pre_call_cache
    async def remove(self, key: K) -> Optional[V]:
        dispatcher: UnaryDispatcher[Optional[V]] = self._request_factory.remove_request(key)
        await dispatcher.dispatch(self._stream_handler)
        return dispatcher.result()

    @_pre_call_cache
    async def remove_mapping(self, key: K, value: V) -> bool:
        dispatcher: UnaryDispatcher[bool] = self._request_factory.remove_mapping_request(key, value)
        await dispatcher.dispatch(self._stream_handler)
        return dispatcher.result()

    @_pre_call_cache
    async def replace(self, key: K, value: V) -> Optional[V]:
        dispatcher: UnaryDispatcher[Optional[V]] = self._request_factory.replace_request(key, value)
        await dispatcher.dispatch(self._stream_handler)
        return dispatcher.result()

    @_pre_call_cache
    async def replace_mapping(self, key: K, old_value: V, new_value: V) -> bool:
        dispatcher: UnaryDispatcher[bool] = self._request_factory.replace_mapping_request(key, old_value, new_value)
        await dispatcher.dispatch(self._stream_handler)
        return dispatcher.result()

    @_pre_call_cache
    async def contains_key(self, key: K) -> bool:
        near_cache: Optional[LocalCache[K, V]] = self._near_cache

        # check the near cache first
        if near_cache is not None:
            result: Optional[V] = await near_cache.get(key)
            if result is not None:
                return True

        dispatcher: UnaryDispatcher[bool] = self._request_factory.contains_key_request(key)
        await dispatcher.dispatch(self._stream_handler)
        return dispatcher.result()

    @_pre_call_cache
    async def contains_value(self, value: V) -> bool:
        dispatcher: UnaryDispatcher[bool] = self._request_factory.contains_value_request(value)
        await dispatcher.dispatch(self._stream_handler)
        return dispatcher.result()

    @_pre_call_cache
    async def is_empty(self) -> bool:
        dispatcher: UnaryDispatcher[bool] = self._request_factory.is_empty_request()
        await dispatcher.dispatch(self._stream_handler)
        return dispatcher.result()

    @_pre_call_cache
    async def size(self) -> int:
        dispatcher: UnaryDispatcher[int] = self._request_factory.size_request()
        await dispatcher.dispatch(self._stream_handler)
        return dispatcher.result()

    @_pre_call_cache
    async def invoke(self, key: K, processor: EntryProcessor[R]) -> Optional[R]:
        dispatcher: UnaryDispatcher[Optional[R]] = self._request_factory.invoke_request(key, processor)
        await dispatcher.dispatch(self._stream_handler)
        return dispatcher.result()

    @_pre_call_cache
    async def invoke_all(
        self, processor: EntryProcessor[R], keys: Optional[set[K]] = None, filter: Optional[Filter] = None
    ) -> AsyncIterator[MapEntry[K, R]]:
        dispatcher: StreamingDispatcher[MapEntry[K, R]] = self._request_factory.invoke_all_request(
            processor, keys, filter
        )
        await dispatcher.dispatch(self._stream_handler)
        return dispatcher

    @_pre_call_cache
    async def aggregate(
        self, aggregator: EntryAggregator[R], keys: Optional[set[K]] = None, filter: Optional[Filter] = None
    ) -> Optional[R]:
        dispatcher: UnaryDispatcher[Optional[R]] = self._request_factory.aggregate_request(aggregator, keys, filter)
        await dispatcher.dispatch(self._stream_handler)
        return dispatcher.result()

    @_pre_call_cache
    async def values(
        self, filter: Optional[Filter] = None, comparator: Optional[Comparator] = None, by_page: bool = False
    ) -> AsyncIterator[V]:
        if by_page and comparator is None and filter is None:
            page_dispatcher: PagingDispatcher[V] = self._request_factory.page_request(values_only=True)
            await page_dispatcher.dispatch(self._stream_handler)
            return page_dispatcher
        else:
            dispatcher: StreamingDispatcher[V] = self._request_factory.values_request(filter, comparator)
            await dispatcher.dispatch(self._stream_handler)
            return dispatcher

    # gTODO
    @_pre_call_cache
    async def keys(self, filter: Optional[Filter] = None, by_page: bool = False) -> AsyncIterator[K]:
        if by_page and filter is None:
            page_dispatcher: PagingDispatcher[K] = self._request_factory.page_request(keys_only=True)
            await page_dispatcher.dispatch(self._stream_handler)
            return page_dispatcher
        else:
            dispatcher: StreamingDispatcher[K] = self._request_factory.keys_request(filter)
            await dispatcher.dispatch(self._stream_handler)
            return dispatcher

    @_pre_call_cache
    async def entries(
        self, filter: Optional[Filter] = None, comparator: Optional[Comparator] = None, by_page: bool = False
    ) -> AsyncIterator[MapEntry[K, V]]:
        if by_page and comparator is None and filter is None:
            page_dispatcher: PagingDispatcher[MapEntry[K, V]] = self._request_factory.page_request()
            await page_dispatcher.dispatch(self._stream_handler)
            return page_dispatcher
        else:
            dispatcher: StreamingDispatcher[MapEntry[K, V]] = self._request_factory.entries_request(filter, comparator)
            await dispatcher.dispatch(self._stream_handler)
            return dispatcher

    @_pre_call_cache
    async def add_index(
        self, extractor: ValueExtractor[T, E], ordered: bool = False, comparator: Optional[Comparator] = None
    ) -> None:
        if extractor is None:
            raise ValueError(_SPECIFY_EXTRACTOR)

        dispatcher: Dispatcher = self._request_factory.add_index_request(extractor, ordered, comparator)
        await dispatcher.dispatch(self._stream_handler)

    @_pre_call_cache
    async def remove_index(self, extractor: ValueExtractor[T, E]) -> None:
        if extractor is None:
            raise ValueError(_SPECIFY_EXTRACTOR)

        dispatcher: Dispatcher = self._request_factory.remove_index_request(extractor)
        await dispatcher.dispatch(self._stream_handler)


class TlsOptions:
    """
    Options specific to the configuration of TLS.
    """

    ENV_CA_CERT = "COHERENCE_TLS_CERTS_PATH"
    """
    Environment variable to configure the path to CA certificates
    """
    ENV_CLIENT_CERT = "COHERENCE_TLS_CLIENT_CERT"
    """
    Environment variable to configure the path to client certificates
    """
    ENV_CLIENT_KEY = "COHERENCE_TLS_CLIENT_KEY"
    """
    Environment variable to configure the path to client key
    """

    def __init__(
        self,
        locked: bool = False,
        enabled: bool = False,
        ca_cert_path: str | None = None,
        client_cert_path: str | None = None,
        client_key_path: str | None = None,
    ) -> None:
        """
        Construct a new :func:`coherence.client.TlsOptions`

        :param locked: If `true`, prevents further mutations to the options.
        :param enabled: Enable/disable TLS support.
        :param ca_cert_path: the path to the CA certificate. If not specified then its configured using the
            environment variable COHERENCE_TLS_CERTS_PATH
        :param client_cert_path: the path to the client certificate. If not specified then its configured using the
            environment variable COHERENCE_TLS_CLIENT_CERT
        :param client_key_path: the path to the client certificate key. If not specified then its configured using the
            environment variable COHERENCE_TLS_CLIENT_KEY
        """
        self._locked = locked
        self._enabled = enabled

        self._ca_cert_path = os.getenv(TlsOptions.ENV_CA_CERT, ca_cert_path)
        self._client_cert_path = os.getenv(TlsOptions.ENV_CLIENT_CERT, client_cert_path)
        self._client_key_path = os.getenv(TlsOptions.ENV_CLIENT_KEY, client_key_path)

    @property
    def enabled(self) -> bool:
        """
        Property to set/get the boolean state if TLS is enabled(true) or disabled(false)
        """
        return self._enabled

    @enabled.setter
    def enabled(self, enabled: bool) -> None:
        if self.is_locked():
            return
        else:
            self._enabled = enabled

    @property
    def ca_cert_path(self) -> Optional[str]:
        """
        Property to set/get the path to the CA certificate
        """
        return self._ca_cert_path

    @ca_cert_path.setter
    def ca_cert_path(self, ca_cert_path: str) -> None:
        if self.is_locked():
            return
        else:
            self._ca_cert_path = ca_cert_path

    @property
    def client_cert_path(self) -> Optional[str]:
        """
        Property to set/get the path to the client certificate.
        """
        return self._client_cert_path

    @client_cert_path.setter
    def client_cert_path(self, client_cert_path: str) -> None:
        if self.is_locked():
            return
        else:
            self._client_cert_path = client_cert_path

    @property
    def client_key_path(self) -> Optional[str]:
        """
        Property to set/get the path to the client certificate key.
        """
        return self._client_key_path

    @client_key_path.setter
    def client_key_path(self, client_key_path: str) -> None:
        if self.is_locked():
            return
        else:
            self._client_key_path = client_key_path

    def locked(self) -> None:
        """
        Once called, no further mutations can be made.
        """
        self._locked = True

    def is_locked(self) -> bool:
        return self._locked

    def __str__(self) -> str:
        return (
            f"TlsOptions(enabled={self.enabled}, ca-cert-path={self.ca_cert_path}, "
            f"client-cert-path={self.client_cert_path}, client-key-path={self.client_key_path})"
        )


class Options:
    """
    Supported :func:`coherence.client.Session` options.
    """

    ENV_SERVER_ADDRESS = "COHERENCE_SERVER_ADDRESS"
    """
    Environment variable to specify the Coherence gRPC server address for the client to connect to. The
    environment variable is used if address is not passed as an argument in the constructor. If the environment
    variable is not set and address is not passed as an argument then `DEFAULT_ADDRESS` is used. One can also
    use the 'coherence' resolver address of "coherence:///host:port" to connect to the Coherence Name
    Service, running on the cluster port, and automatically discover the gRPC proxy addresses and one of them
    will be randomly picked.
    """
    ENV_REQUEST_TIMEOUT = "COHERENCE_CLIENT_REQUEST_TIMEOUT"
    """
    Environment variable to specify the request timeout for each remote call. The environment variable is used if
    request timeout is not passed as an argument in the constructor. If the environment variable is not set and
    request timeout is not passed as an argument then `DEFAULT_REQUEST_TIMEOUT` of 30 seconds is used
    """
    ENV_READY_TIMEOUT = "COHERENCE_READY_TIMEOUT"
    """
    Environment variable to specify the maximum amount of time an NamedMap or NamedCache operations may wait for the
    underlying gRPC channel to be ready.  This is independent of the request timeout which sets a deadline on how
    long the call may take after being dispatched.
    """
    ENV_SESSION_DISCONNECT_TIMEOUT = "COHERENCE_SESSION_DISCONNECT_TIMEOUT"
    """
    Environment variable to specify the maximum amount of time, in seconds, a Session may remain in a disconnected
    state without successfully reconnecting.
    """

    DEFAULT_ADDRESS: Final[str] = "localhost:1408"
    """The default target address to connect to Coherence gRPC server."""
    DEFAULT_SCOPE: Final[str] = ""
    """The default scope."""
    DEFAULT_REQUEST_TIMEOUT: Final[float] = 30.0
    """The default request timeout."""
    DEFAULT_READY_TIMEOUT: Final[float] = 0
    """
    The default ready timeout is 0 which disables the feature by default.  Explicitly configure the ready timeout
    session option or use the environment variable to specify a positive value indicating how many seconds an RPC will
    wait for the underlying channel to be ready before failing.
    """
    DEFAULT_SESSION_DISCONNECT_TIMEOUT: Final[float] = 30.0
    """
    The default maximum time a session may be in a disconnected state without having successfully reconnected.
    """
    DEFAULT_FORMAT: Final[str] = "json"
    """The default serialization format"""

    def __init__(
        self,
        address: str = DEFAULT_ADDRESS,
        scope: str = DEFAULT_SCOPE,
        request_timeout_seconds: float = DEFAULT_REQUEST_TIMEOUT,
        ready_timeout_seconds: float = DEFAULT_READY_TIMEOUT,
        session_disconnect_seconds: float = DEFAULT_SESSION_DISCONNECT_TIMEOUT,
        ser_format: str = DEFAULT_FORMAT,
        channel_options: Optional[Sequence[Tuple[str, Any]]] = None,
        tls_options: Optional[TlsOptions] = None,
    ) -> None:
        """
        Construct a new :func:`coherence.client.Options`

        :param address: Address of the target Coherence cluster gRPC endpoint of the form "host:port" to connect to.
          If not explicitly set, this defaults to :func:`coherence.client.Options.DEFAULT_ADDRESS`. See
          also :func:`coherence.client.Options.ENV_SERVER_ADDRESS`. One can also use the 'coherence' gRPC resolver
          address of "coherence:///host:port" to connect to the Coherence Name Service, running on the
          cluster port, and automatically discover the gRPC endpoints.
        :param scope: scope name used to link this :func:`coherence.client.Options` to the
          corresponding `ConfigurableCacheFactory` on the server.
        :param request_timeout_seconds: Defines the request timeout, in `seconds`, that will be applied to each
          remote call. If not explicitly set, this defaults to :func:`coherence.client.Options.DEFAULT_REQUEST_TIMEOUT`.
          See also :func:`coherence.client.Options.ENV_REQUEST_TIMEOUT`
        :param ready_timeout_seconds: Defines the ready timeout, in `seconds`.  If this is a positive
          float value, remote calls will not fail immediately if no connection is available.  If this is a value of zero
          or less, then remote calls will fail-fast.  If not explicitly configured, the default of 0 is assumed.

          See also :class:`coherence.client.Options.ENV_READY_TIMEOUT`
        :param session_disconnect_seconds: Defines the maximum time, in `seconds`, that a session may remain in
          a disconnected state without successfully reconnecting.
        :param ser_format: The serialization format.  Currently, this is always `json`
        :param channel_options: The `gRPC` `ChannelOptions`. See
            https://grpc.github.io/grpc/python/glossary.html#term-channel_arguments and
            https://github.com/grpc/grpc/blob/master/include/grpc/impl/grpc_types.h
        :param tls_options: Optional TLS configuration.
        """
        self._address = os.getenv(Options.ENV_SERVER_ADDRESS, address)

        self._request_timeout_seconds = Options._get_float_from_env(
            Options.ENV_REQUEST_TIMEOUT, request_timeout_seconds
        )
        self._ready_timeout_seconds = Options._get_float_from_env(Options.ENV_READY_TIMEOUT, ready_timeout_seconds)
        self._session_disconnect_timeout_seconds = Options._get_float_from_env(
            Options.ENV_SESSION_DISCONNECT_TIMEOUT, session_disconnect_seconds
        )

        self._scope = scope
        self._ser_format = ser_format

        if channel_options is not None:
            self._channel_options = channel_options

        if tls_options is not None:
            self._tls_options = tls_options

    async def _resolve_ns_address(self) -> None:
        if self.address.startswith("coherence:///"):
            # Remove the prefix and split into host and port
            _, ns_addr = self._address.split("coherence:///", 1)

            # Resolve to grpc address from nameservice address
            self._address = await AsyncNSLookup._resolve_nslookup_address(ns_addr)

    @property
    def tls_options(self) -> Optional[TlsOptions]:
        """
        Returns the TLS-specific configuration options.

        :return: the TLS-specific configuration options.
        """
        return getattr(self, "_tls_options", None)

    @tls_options.setter
    def tls_options(self, tls_options: TlsOptions) -> None:
        """
        Sets the TLS-specific configuration options.

        :param tls_options: the TLS-specific configuration options.
        """
        self._tls_options = tls_options

    @property
    def address(self) -> str:
        """
        Return the IPv4 host address and port in the format of ``[host]:[port]``.

        :return: the IPv4 host address and port in the format of ``[host]:[port]``.
        """
        return self._address

    @property
    def scope(self) -> str:
        """
        Return the scope name used to link this `Session` with to the corresponding `ConfigurableCacheFactory` on the
        server.

        :return: the scope name used to link this `Session` with to the corresponding `ConfigurableCacheFactory` on the
         server.
        """
        return self._scope

    @property
    def format(self) -> str:
        """
        The serialization format used by this session.  This library currently supports JSON serialization only,
        thus this always returns 'json'.

        :return: the serialization format used by this session.
        """
        return self._ser_format

    @property
    def request_timeout_seconds(self) -> float:
        """
        Returns the request timeout in `seconds`

        :return: the request timeout in `seconds`
        """
        return self._request_timeout_seconds

    @property
    def ready_timeout_seconds(self) -> float:
        """
        Returns the ready timeout in `seconds`.

        :return: the ready timeout in `seconds`
        """
        return self._ready_timeout_seconds

    @property
    def session_disconnect_timeout_seconds(self) -> float:
        """
        Returns the ready timeout in `seconds`.

        :return: the ready timeout in `seconds`
        """
        return self._session_disconnect_timeout_seconds

    @property
    def channel_options(self) -> Optional[Sequence[Tuple[str, Any]]]:
        """
        Return the `gRPC` `ChannelOptions`.

        :return: the `gRPC` `ChannelOptions`.
        """
        return getattr(self, "_channel_options", None)

    @channel_options.setter
    def channel_options(self, channel_options: Sequence[Tuple[str, Any]]) -> None:
        """
        Set the `gRPC` `ChannelOptions`.

        :param channel_options: the `gRPC` `ChannelOptions`.
        """
        self._channel_options = channel_options

    @staticmethod
    def _get_float_from_env(variable_name: str, default_value: float) -> float:
        """
        Return a float value parsed from the provided environment variable name.

        :param variable_name: the environment variable name
        :param default_value: the value to use if the environment variable is not set

        :return: the float value from the environment or the default if the value can't be parsed
          or the environment variable is not set
        """
        timeout = os.getenv(variable_name)
        if timeout is not None:
            time_out: float = default_value
            try:
                time_out = float(timeout)
            except ValueError:
                COH_LOG.warning(
                    "The timeout value of [%s] specified by environment variable [%s] cannot be converted to a float",
                    timeout,
                    variable_name,
                )

            return time_out
        else:
            return default_value

    def __str__(self) -> str:
        return (
            f"Options(address={self.address}, scope={self.scope}, format={self.format},"
            f" request-timeout-seconds={self.request_timeout_seconds}, "
            f"ready-timeout-seconds={self.ready_timeout_seconds}, "
            f"session-disconnect-timeout-seconds={self.session_disconnect_timeout_seconds}, "
            f"tls-options={self.tls_options}, "
            f"channel-options={self.channel_options})"
        )


def _get_channel_creds(tls_options: TlsOptions) -> grpc.ChannelCredentials:
    client_cert: bytes | None = None
    client_key: bytes | None = None
    ca_cert: bytes | None = None

    if tls_options.client_cert_path is not None:
        with open(tls_options.client_cert_path, "rb") as f:
            client_cert = f.read()
    if tls_options.client_key_path is not None:
        with open(tls_options.client_key_path, "rb") as f:
            client_key = f.read()
    if tls_options.ca_cert_path is not None:
        with open(tls_options.ca_cert_path, "rb") as f:
            ca_cert = f.read()

    credentials = grpc.ssl_channel_credentials(ca_cert, client_key, client_cert)

    return credentials


class Session:
    """
    Session represents a logical connection to an endpoint. It also acts as a factory for creating caches.

    This class emits the following events:

        1. :class:`coherence.event.MapLifecycleEvent.DESTROYED`: when the underlying cache is destroyed
        2. :class:`coherence.event.MapLifecycleEvent.TRUNCATED`: When the underlying cache is truncated
        3. :class:`coherence.event.MapLifecycleEvent.RELEASED`: When the underlying cache is released
        4. :class:`coherence.event.SessionLifecycleEvent.CONNECT`: when the Session detects the underlying `gRPC`
            channel has connected.
        5. :class:`coherence.event.SessionLifecycleEvent.DISCONNECT`: when the Session detects the underlying `gRPC`
            channel has disconnected
        6. :class:`coherence.event.SessionLifecycleEvent.RECONNECTED`: when the Session detects the underlying `gRPC`
            channel has re-connected
        7. :class:`coherence.event.SessionLifecycleEvent.CLOSED`: when the Session has been closed

    """

    def __init__(self, session_options: Optional[Options] = None):
        """
        Construct a new `Session` based on the provided :func:`coherence.client.Options`

        :param session_options: the provided :func:`coherence.client.Options`
        """
        self._closed: bool = False
        self._session_id: str = str(uuid.uuid4())
        self._ready: bool = False
        self._initialized: bool = False
        self._ready_condition: Condition = Condition()
        self._caches: dict[str, NamedCache[Any, Any]] = dict()
        self._lock: asyncio.Lock = asyncio.Lock()
        if session_options is not None:
            self._session_options = session_options
        else:
            self._session_options = Options()

        self._ready_timeout_seconds: float = self._session_options.ready_timeout_seconds
        self._ready_enabled: bool = self._ready_timeout_seconds > 0

        interceptors = [
            _InterceptorUnaryUnary(self),
            _InterceptorUnaryStream(self),
            _InterceptorStreamUnary(self),
        ]

        # only add the StreamStream interceptor if ready support is enabled as
        # when added in the non-ready case, the call will not fail-fast
        if self._ready_enabled:
            interceptors.append(_InterceptorStreamStream(self))

        self._tasks: Set[Task[None]] = set()

        options: Sequence[tuple[str, Any]] = [
            ("grpc.min_reconnect_backoff_ms", 1100),
            ("grpc.max_reconnect_backoff_ms", 3000),
            ("grpc.lb_policy_name", "round_robin"),
        ]

        self._is_server_grpc_v1 = False
        self._v1_init_response_details: dict[str, Any] = dict()

        if self._session_options.tls_options is None:
            self._channel: grpc.aio.Channel = grpc.aio.insecure_channel(
                self._session_options.address,
                options=(
                    options if self._session_options.channel_options is None else self._session_options.channel_options
                ),
                interceptors=interceptors,
            )
        else:
            creds: grpc.ChannelCredentials = _get_channel_creds(self._session_options.tls_options)
            self._channel = grpc.aio.secure_channel(
                self._session_options.address,
                creds,
                options=(
                    options if self._session_options.channel_options is None else self._session_options.channel_options
                ),
                interceptors=interceptors,
            )

        self._handshake = _Handshake(self)

        watch_task: Task[None] = asyncio.create_task(watch_channel_state(self))
        self._tasks.add(watch_task)
        self._emitter: EventEmitter = EventEmitter()
        self._channel.get_state(True)  # trigger connect

    @staticmethod
    async def create(session_options: Optional[Options] = None) -> Session:
        if session_options is None:
            session_options = Options()
        await session_options._resolve_ns_address()
        session: Session = Session(session_options)
        await session._set_ready(False)
        await session._handshake.handshake()
        if session._protocol_version > 0:
            COH_LOG.info(
                f"Session(id={session.session_id}, connected to [{session._session_options.address}]"
                f" proxy-version={session._proxy_version}, protocol-version={session._protocol_version}"
                f" proxy-member-id={session._proxy_member_id})"
            )
        else:
            COH_LOG.info(
                f"Session(id={session.session_id}, connected to [{session._session_options.address}]"
                f" protocol-version={session._protocol_version})"
            )
        return session

    # noinspection PyTypeHints
    @_pre_call_session
    def on(
        self,
        event: Literal[MapLifecycleEvent.DESTROYED] | Literal[MapLifecycleEvent.RELEASED] | SessionLifecycleEvent,
        callback: Callable[[str], None] | Callable[[], None],
    ) -> None:
        """
        Register a callback to be invoked when the following events are raised:

        * MapLifecycleEvent.DESTROYED
        * MapLifecycleEvent.RELEASED
        * Any SessionLifecycleEvent

        The callbacks defined for MapLifecycleEvent DESTROYED and RELEASED should accept a single string
        argument representing the cache name that the event was raised for.

        The SessionLifecycleEvent callbacks should not accept call arguments.
        :param event:     the event to listener for
        :param callback:  the callback to invoke when the event is raised
        """
        if event == SessionLifecycleEvent.CONNECTED and self.is_ready():
            callback()  # type: ignore
            return

        self._emitter.on(str(event.value), callback)

    @property
    def channel(self) -> grpc.aio.Channel:
        """
        Return the underlying `gRPC` Channel used by this session.

        :return: the underlying `gRPC` Channel used by this session.
        """
        return self._channel

    @property
    def scope(self) -> str:
        """
        Return the scope name used to link this `Session` with to the corresponding `ConfigurableCacheFactory` on the
        server.

        :return: the scope name used to link this `Session` with to the corresponding `ConfigurableCacheFactory` on the
          server.
        """
        return self._session_options.scope

    @property
    def format(self) -> str:
        """
        Returns the default serialization format used by the `Session`

        :return: the default serialization format used by the `Session`
        """
        return self._session_options.format

    @property
    def options(self) -> Options:
        """
        Return the :func:`coherence.client.Options` (read-only) used to configure this session.

        :return: the :func:`coherence.client.Options` (read-only) used to configure this session.
        """
        return self._session_options

    @property
    def closed(self) -> bool:
        """
        Returns `True` if Session is closed else `False`.

        :return: `True` if Session is closed else `False`
        """
        return self._closed

    @property
    def session_id(self) -> str:
        """
        Returns this Session's ID.

        :return: this Session's ID
        """
        return self._session_id

    def __str__(self) -> str:
        if self._protocol_version > 0:
            return (
                f"Session(id={self.session_id}, closed={self.closed}, state={self._channel.get_state(False)},"
                f" caches/maps={len(self._caches)}, protocol-version={self._protocol_version} options={self.options}"
                f" proxy-version={self._proxy_version}, proxy-member-id={self._proxy_member_id})"
            )
        else:
            return (
                f"Session(id={self.session_id}, closed={self.closed}, state={self._channel.get_state(False)},"
                f" caches/maps={len(self._caches)}, protocol-version={self._protocol_version} options={self.options})"
            )

    # noinspection PyProtectedMember
    @_pre_call_session
    async def get_cache(self, name: str, cache_options: Optional[CacheOptions] = None) -> NamedCache[K, V]:
        """
        Returns a :func:`coherence.client.NamedCache` for the specified cache name.

        :param name: the cache name
        :param cache_options: a :class:`coherence.client.CacheOptions`

        :return: Returns a :func:`coherence.client.NamedCache` for the specified cache name.
        """
        serializer = SerializerRegistry.serializer(self._session_options.format)

        async with self._lock:
            c = self._caches.get(name)
            if c is None:
                if self._protocol_version == 0:
                    c = NamedCacheClient(name, self, serializer, cache_options)
                    # initialize the event stream now to ensure lifecycle listeners will work as expected
                    await c._events_manager._ensure_stream()
                else:
                    c = NamedCacheClientV1(name, self, serializer, cache_options)
                    await c._ensure_cache()
                    await c._post_create()

                self._setup_event_handlers(c)
                self._caches.update({name: c})
            else:
                if c.options != cache_options:
                    raise ValueError(
                        "A NamedMap or NamedCache with the same name already exists with different CacheOptions"
                    )
            return c

    # noinspection PyProtectedMember
    @_pre_call_session
    async def get_map(self, name: str, cache_options: Optional[CacheOptions] = None) -> NamedMap[K, V]:
        """
        Returns a :func:`coherence.client.NameMap` for the specified cache name.

        :param name: the map name
        :param cache_options: a :class:`coherence.client.CacheOptions`

        :return: Returns a :func:`coherence.client.NamedMap` for the specified cache name.
        """
        return cast(NamedMap[K, V], await self.get_cache(name, cache_options))

    def is_ready(self) -> bool:
        """
        Returns
        :return:
        """
        if self._closed:
            return False

        return True if not self._ready_enabled else self._ready

    @property
    def _proxy_version(self) -> str:
        return self._handshake.proxy_version

    @property
    def _protocol_version(self) -> int:
        return self._handshake.protocol_version

    @property
    def _proxy_member_id(self) -> int:
        return self._handshake.proxy_member_id

    async def _set_ready(self, ready: bool) -> None:
        self._ready = ready
        if self._ready:
            if not self._ready_condition.locked():
                await self._ready_condition.acquire()
            self._ready_condition.notify_all()
            self._ready_condition.release()
        else:
            await self._ready_condition.acquire()

    async def _wait_for_ready(self) -> None:
        if self._ready_enabled and not self.is_ready():
            timeout: float = self._ready_timeout_seconds
            COH_LOG.debug(f"Waiting for session {self.session_id} to become active; timeout=[{timeout} seconds]")
            try:
                await asyncio.wait_for(self._ready_condition.wait(), timeout)
            except TimeoutError:
                s = "Deadline [{0} seconds] exceeded " "waiting for session {1} to become active".format(
                    str(timeout), self.session_id
                )
                raise TimeoutError(s)

    # noinspection PyUnresolvedReferences
    async def close(self) -> None:
        """
        Close the `Session`
        """
        if not self._closed:
            self._closed = True
            self._emitter.emit(SessionLifecycleEvent.CLOSED.value)
            for task in self._tasks:
                task.cancel()
                await task
            self._tasks.clear()

            caches_copy: dict[str, NamedCache[Any, Any]] = self._caches.copy()
            for cache in caches_copy.values():
                await cache.release()

            self._caches.clear()

            await self._channel.close()  # TODO: consider grace period?
            self._channel = None

    def _setup_event_handlers(self, client: NamedCacheClient[K, V] | NamedCacheClientV1[K, V]) -> None:
        this: Session = self

        def on_destroyed(name: str) -> None:
            if name in this._caches:
                del this._caches[name]
            self._emitter.emit(MapLifecycleEvent.DESTROYED.value, name)

        def on_released(name: str) -> None:
            if name in this._caches:
                del this._caches[name]
            self._emitter.emit(MapLifecycleEvent.RELEASED.value, name)

        client.on(MapLifecycleEvent.DESTROYED, on_destroyed)
        client.on(MapLifecycleEvent.RELEASED, on_released)


# noinspection PyArgumentList
class _BaseInterceptor:
    """Base client interceptor to enable waiting for channel connectivity and
    set call timeouts.
    Having this base class and four concrete implementations is due to
    https://github.com/grpc/grpc/issues/31442"""

    def __init__(self, session: Session):
        self._session: Session = session

    @no_type_check  # disabling as typing info in gRPC is in protected packages
    async def _do_intercept(self, continuation, client_call_details, request):
        """
        Intercepts a gRPC call setting our specific options for the call.
        :param continuation:         the gRPC call continuation
        :param client_call_details:  the call details
        :param request:              the gRPC request (if any)
        :return:                     the result of the call
        """
        from . import _TIMEOUT_CONTEXT_VAR

        new_details = grpc.aio.ClientCallDetails(
            client_call_details.method,
            _TIMEOUT_CONTEXT_VAR.get(self._session.options.request_timeout_seconds),
            client_call_details.metadata,
            client_call_details.credentials,
            True if self._session._ready_enabled else None,
        )
        return await continuation(new_details, request)


class _InterceptorUnaryUnary(_BaseInterceptor, grpc.aio.UnaryUnaryClientInterceptor):
    """Interceptor for Unary/Unary calls."""

    @no_type_check  # disabling as typing info in gRPC is in protected packages
    async def intercept_unary_unary(self, continuation, client_call_details, request):
        return await self._do_intercept(continuation, client_call_details, request)


class _InterceptorUnaryStream(_BaseInterceptor, grpc.aio.UnaryStreamClientInterceptor):
    """Interceptor for Unary/Stream calls."""

    @no_type_check  # disabling as typing info in gRPC is in protected packages
    async def intercept_unary_stream(self, continuation, client_call_details, request):
        return await self._do_intercept(continuation, client_call_details, request)


class _InterceptorStreamUnary(_BaseInterceptor, grpc.aio.StreamUnaryClientInterceptor):
    """Interceptor for Stream/Unary calls."""

    @no_type_check  # disabling as typing info in gRPC is in protected packages
    async def intercept_stream_unary(self, continuation, client_call_details, request):
        return await self._do_intercept(continuation, client_call_details, request)


class _InterceptorStreamStream(_BaseInterceptor, grpc.aio.StreamStreamClientInterceptor):
    """Interceptor for Stream/Stream calls."""

    # noinspection PyArgumentList,PyUnresolvedReferences
    @no_type_check  # disabling as typing info in gRPC is in protected packages
    async def intercept_stream_stream(self, continuation, client_call_details, request):
        new_details = grpc.aio.ClientCallDetails(
            client_call_details.method,
            client_call_details.timeout,
            client_call_details.metadata,
            client_call_details.credentials,
            True,
        )

        return await continuation(new_details, request)


# noinspection PyProtectedMember
async def watch_channel_state(session: Session) -> None:
    emitter: EventEmitter = session._emitter
    channel: grpc.aio.Channel = session.channel
    first_connect: bool = True
    connected: bool = False
    last_state: grpc.ChannelConnectivity = grpc.ChannelConnectivity.IDLE
    disconnect_time: float = 0

    def current_milli_time() -> float:
        return round(time.time() * 1000)

    try:
        while True:
            state: grpc.ChannelConnectivity = channel.get_state(True)
            if COH_LOG.isEnabledFor(logging.DEBUG):
                COH_LOG.debug(f"New Channel State: transitioning from [{last_state}] to [{state}].")
            if state == grpc.ChannelConnectivity.SHUTDOWN:
                COH_LOG.info(f"Session [{session.session_id}] terminated.")
                await session._set_ready(False)
                await session.close()
                return
            elif state == grpc.ChannelConnectivity.READY:
                if not first_connect and not connected:
                    connected = True
                    disconnect_time = 0
                    COH_LOG.info(f"Session [{session.session_id} re-connected to [{session.options.address}].")
                    await emitter.emit_async(SessionLifecycleEvent.RECONNECTED.value)
                    await session._set_ready(True)
                elif first_connect and not connected:
                    connected = True
                    COH_LOG.info(f"Session [{session.session_id}] connected to [{session.options.address}].")

                    first_connect = False
                    await emitter.emit_async(SessionLifecycleEvent.CONNECTED.value)
                    await session._set_ready(True)
            else:
                if connected:
                    connected = False
                    disconnect_time = -1
                    COH_LOG.warning(
                        f"Session [{session.session_id}] disconnected from [{session.options.address}];"
                        f" will attempt reconnect."
                    )

                    await emitter.emit_async(SessionLifecycleEvent.DISCONNECTED.value)
                    await session._set_ready(False)

                if disconnect_time != 0:
                    if disconnect_time == -1:
                        disconnect_time = current_milli_time()
                    else:
                        waited: float = current_milli_time() - disconnect_time
                        timeout = session.options.session_disconnect_timeout_seconds
                        if COH_LOG.isEnabledFor(logging.DEBUG):
                            COH_LOG.debug(
                                f"Waited [{waited / 1000} seconds] for session [{session.session_id}] to reconnect."
                                f" [~{(round(timeout - (waited / 1000)))} seconds] remaining to reconnect."
                            )
                        if waited >= timeout:
                            COH_LOG.error(
                                f"session [{session.session_id}] unable to reconnect within [{timeout} seconds."
                                f"  Closing session."
                            )
                            await session.close()
                            return

            state = channel.get_state(True)
            if COH_LOG.isEnabledFor(logging.DEBUG):
                COH_LOG.debug(f"Waiting for state change from [{state}]")
            await channel.wait_for_state_change(state)
    except asyncio.CancelledError:
        return


class _Stream(abc.ABC, AsyncIterator[T]):
    """
    A simple AsyncIterator that wraps a Callable that produces iteration
    elements.
    """

    def __init__(
        self,
        serializer: Serializer,
        stream: grpc.Channel.unary_stream,
        next_producer: Callable[[Serializer, grpc.Channel.unary_stream], Awaitable[T]],
    ) -> None:
        super().__init__()
        # A function that may be called to produce a series of results
        self._next_producer = next_producer

        # the Serializer that should be used to deserialize results
        self._serializer = serializer

        # the gRPC stream providing results
        self._stream = stream

    def __aiter__(self) -> AsyncIterator[T]:
        return self

    def __anext__(self) -> Awaitable[T]:
        return self._next_producer(self._serializer, self._stream)


# noinspection PyProtectedMember
class _PagedStream(abc.ABC, AsyncIterator[T]):
    """
    An AsyncIterator that will stream results in pages.
    """

    def __init__(
        self, client: NamedCacheClient[K, V], result_handler: Callable[[Serializer, Any], Any], keys: bool = False
    ) -> None:
        super().__init__()
        # flag indicating that all pages have been processed
        self._exhausted: bool = False

        # the gRPC client
        self._client: NamedCacheClient[K, V] = client

        # the handler responsible for deserializing the result
        self._result_handler: Callable[[Serializer, Any], Any] = result_handler

        # the serializer to be used when deserializing streamed results
        self._serializer: Serializer = client._request_factory.serializer

        # cookie that tracks page streaming; used for each new page request
        self._cookie: bytes = bytes()

        # the gRPC stream providing the results
        self._stream: grpc.Channel.unary_stream = None

        # flag indicating a new page has been loaded
        self._new_page: bool = True

        # flag indicating that pages will be keys only
        self._keys: bool = keys

    def __aiter__(self) -> AsyncIterator[T]:
        return self

    async def __anext__(self) -> T:
        # keep the loop running to ensure we don't exit
        # prematurely which would result in a None value
        # being returned incorrectly between pages
        while True:
            if self._stream is None and not self._exhausted:
                await self.__load_next_page()

            if self._stream is None and self._exhausted:
                raise StopAsyncIteration

            async for item in self._stream:
                if self._new_page:  # a new page has been loaded; the cookie will be the first result
                    self._new_page = False
                    self._cookie = item.value if self._keys else item.cookie
                    if self._cookie == b"":
                        self._exhausted = True  # processing the last page
                else:
                    return self._result_handler(self._serializer, item)

            self._stream = None
            if self._exhausted:
                raise StopAsyncIteration

    # noinspection PyProtectedMember
    async def __load_next_page(self) -> None:
        """
        Requests the next page of results to be streamed.

        :return: None
        """
        request: PageRequest = self._client._request_factory.page_request(self._cookie)
        self._stream = self._get_stream(request)
        self._new_page = True

    def _get_stream(self, request: PageRequest) -> grpc.Channel.unary_stream:
        """
        Obtain the gRPC unary_stream for the provided PageRequest.

        :param request: the PageRequest
        :return: the gRPC unary_stream for the given request
        """
        client_stub: NamedCacheServiceStub = self._client._client_stub
        return client_stub.nextKeySetPage(request) if self._keys else client_stub.nextEntrySetPage(request)


def _scalar_deserializer(serializer: Serializer, item: Any) -> Any:
    """
    Helper method to deserialize a key or value returned in a stream.

    :param serializer: the serializer that should be used
    :param item: the key or value to deserialize
    :return: the deserialized key or value
    """
    return serializer.deserialize(item.value)


def _entry_deserializer(serializer: Serializer, item: Any) -> MapEntry[Any, Any]:
    """
    Helper method to deserialize entries returned in a stream.

    :param serializer: the serializer that should be used to deserialize the entry
    :param item: the entry
    :return: the deserialized entry
    """
    return MapEntry(serializer.deserialize(item.key), serializer.deserialize(item.value))


async def _scalar_producer(serializer: Serializer, stream: grpc.Channel.unary_stream) -> T:
    """
    Helper method to iterate over a stream and produce scalar results.

    :param serializer: the serializer that should be used to deserialize the scalar value
    :param stream: the gRPC stream
    :return: one or more deserialized scalar values
    """
    async for item in stream:
        return _scalar_deserializer(serializer, item)
    raise StopAsyncIteration


async def _entry_producer(serializer: Serializer, stream: grpc.Channel.unary_stream) -> MapEntry[K, V]:
    """
    Helper method to iterate over a stream and produce MapEntry instances
    .
    :param serializer: the serializer that should be used to deserialize the entry
    :param stream: the gRPC stream
    :return: one or more deserialized MapEntry instances
    """
    async for item in stream:
        return _entry_deserializer(serializer, item)
    raise StopAsyncIteration


async def _entry_producer_from_list(serializer: Serializer, the_list: list[Any]) -> MapEntry[K, V]:  # type: ignore
    if len(the_list) == 0:
        raise StopAsyncIteration
    for item in the_list:
        the_list.pop(0)
        return _entry_deserializer(serializer, item)


class _ListAsyncIterator(abc.ABC, AsyncIterator[T]):
    def __init__(
        self,
        serializer: Serializer,
        the_list: list[T],
        next_producer: Callable[[Serializer, list[T]], Awaitable[T]],
    ) -> None:
        super().__init__()
        # A function that may be called to produce a series of results
        self._next_producer = next_producer

        # the Serializer that should be used to deserialize results
        self._serializer = serializer

        # the gRPC stream providing results
        self._the_list = the_list

    def __aiter__(self) -> AsyncIterator[T]:
        return self

    def __anext__(self) -> Awaitable[T]:
        return self._next_producer(self._serializer, self._the_list)


# noinspection PyProtectedMember
class StreamHandler:
    # noinspection PyTypeChecker
    def __init__(
        self,
        session: Session,
        request_factory: RequestFactoryV1,
        events_manager: _MapEventsManagerV1[K, V],
    ):
        self._debug: str = os.environ.get("COHERENCE_MESSAGING_DEBUG", "off")
        self._session: Session = session
        self._channel = session.channel
        self._reconnect_timeout: float = session.options.session_disconnect_timeout_seconds
        self._proxy_stub = ProxyServiceStub(session.channel)

        self._request_factory: RequestFactoryV1 = request_factory
        self._events_manager: _MapEventsManagerV1[K, V] = events_manager
        self._stream: Optional[StreamStreamMultiCallable] = None
        self._observers: dict[int, ResponseObserver] = dict()
        self.result_available = Event()
        self.result_available.clear()
        self._background_tasks: Set[Task[Any]] = set()
        self._closed: bool = False
        self._connected = Event()
        self._connected.clear()
        self._ensure_lock = asyncio.Lock()
        self._write_lock = asyncio.Lock()

        task = asyncio.create_task(self.handle_response())
        task.add_done_callback(self._background_tasks.discard)
        self._background_tasks.add(task)

        def on_disconnect() -> None:
            self._connected.clear()
            self._stream = None

        async def on_reconnect() -> None:
            self._connected.set()
            # noinspection PyUnresolvedReferences
            await self._events_manager._named_map._ensure_cache()
            await self._events_manager._reconnect()

        session.on(SessionLifecycleEvent.DISCONNECTED, on_disconnect)
        session.on(SessionLifecycleEvent.RECONNECTED, on_reconnect)

    def _log_message(self, message: Any, send: bool = True) -> None:
        debug: str = self._debug

        if debug != sys.intern("off"):
            session_id = self._session.session_id
            prefix: str = f"c.m.d SND [{session_id}] -> " if send else f"c.m.d RCV [{session_id}] <- "
            if debug == sys.intern("on"):
                COH_LOG.debug(prefix + textwrap.shorten(MessageToJson(message=message, indent=None), 256))
            elif debug == sys.intern("full"):
                COH_LOG.debug(prefix + MessageToJson(message=message, indent=None))

    @property
    async def stream(self) -> StreamStreamMultiCallable:
        await self._ensure_stream()

        return self._stream

    # noinspection PyUnresolvedReferences
    async def close(self) -> None:
        tasks: Set[Task[Any]] = set(self._background_tasks)
        for task in tasks:
            task.cancel()
            await task

        if self._stream is not None:
            self._stream.cancel()
            self._stream = None

        self._closed = True

    async def _ensure_stream(self) -> StreamStreamMultiCallable:
        if self._stream is None:
            async with self._ensure_lock:
                if self._stream is None:
                    stream = self._proxy_stub.subChannel()

                    try:
                        await stream.write(self._request_factory.init_sub_channel())
                    except grpc.aio._call.AioRpcError as e:
                        print(e)

                    await stream.read()
                    self._stream = stream  # we don't care about the result, only that it completes
                    self._connected.set()

        return self._stream

    # noinspection PyUnresolvedReferences
    async def send_proxy_request(self, proxy_request: ProxyRequest) -> None:
        stream: StreamStreamMultiCallable = await self.stream

        self._log_message(proxy_request)

        async with self._write_lock:
            await stream.write(proxy_request)

    def register_observer(self, observer: ResponseObserver) -> None:
        assert observer.id not in self._observers

        self._observers[observer.id] = observer

    def deregister_observer(self, observer: ResponseObserver) -> None:
        self._observers.pop(observer.id, None)

    async def handle_response(self) -> None:
        while not self._closed:
            try:
                stream: StreamStreamMultiCallable = await self.stream
                # noinspection PyUnresolvedReferences
                response = await stream.read()
                response_id = response.id

                self._log_message(response, False)

                if response_id == 0:
                    await self.handle_zero_id_response(response)
                else:
                    if response.HasField("message"):
                        observer = self._observers.get(response_id, None)
                        if observer is not None:
                            named_cache_response = NamedCacheResponse()
                            response.message.Unpack(named_cache_response)
                            observer._next(named_cache_response)
                            continue
                    elif response.HasField("init"):
                        self.result_available.set()
                    elif response.HasField("error"):
                        observer = self._observers.get(response_id, None)
                        if observer is not None:
                            self._observers.pop(response_id, None)
                            observer._err(Exception(response.error.message))
                        continue
                    elif response.HasField("complete"):
                        observer = self._observers.get(response_id, None)
                        if observer is not None:
                            self._observers.pop(response_id, None)
                            observer._done()
            except asyncio.CancelledError:
                return
            except grpc.aio._call.AioRpcError as e:
                if e.code().name == "CANCELLED":
                    continue
                COH_LOG.error("Received unexpected error from proxy: " + str(e))

    # noinspection PyUnresolvedReferences
    async def handle_zero_id_response(self, response: ProxyResponse) -> None:
        if response.HasField("message"):
            named_cache_response = NamedCacheResponse()
            response.message.Unpack(named_cache_response)
            response_type = named_cache_response.type
            if response_type == ResponseType.Message:
                return
            elif response_type == ResponseType.MapEvent:
                # Handle MapEvent Response
                event_response = MapEventMessage()
                named_cache_response.message.Unpack(event_response)

                if event_response.id == 0:
                    # v0 map event received - drop on the floor
                    return

                try:
                    event: MapEvent[Any, Any] = MapEvent(
                        self._events_manager._named_map, event_response, self._events_manager._serializer
                    )
                    for _id in event_response.filterIds:
                        filter_group: Optional[_ListenerGroup[Any, Any, Any]] = (
                            self._events_manager._filter_id_listener_group_map.get(_id, None)
                        )
                        if filter_group is not None:
                            await filter_group._notify_listeners(event)

                    key_group = self._events_manager._key_map.get(event.key, None)
                    if key_group is not None:
                        await key_group._notify_listeners(event)
                except Exception as e:
                    traceback.print_exc()
                    COH_LOG.warning("Unhandled Event Message: " + str(e))
            elif response_type == ResponseType.Destroyed:
                if self._events_manager._named_map.cache_id == named_cache_response.cacheId:
                    self._events_manager._emitter.emit(
                        MapLifecycleEvent.DESTROYED.value, self._events_manager._named_map.name
                    )
            elif response_type == ResponseType.Truncated:
                if self._events_manager._named_map.cache_id == named_cache_response.cacheId:
                    self._events_manager._emitter.emit(
                        MapLifecycleEvent.TRUNCATED.value, self._events_manager._named_map.name
                    )
