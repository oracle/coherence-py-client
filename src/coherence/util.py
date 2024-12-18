# Copyright (c) 2022, 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

import asyncio
import sys
import threading
import time
from abc import ABC, abstractmethod
from asyncio import Event
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Callable, Generic, Optional, Tuple, TypeVar

from google.protobuf.any_pb2 import Any as GrpcAny
from google.protobuf.wrappers_pb2 import BoolValue, BytesValue, Int32Value

from .aggregator import EntryAggregator
from .cache_service_messages_v1_pb2 import EnsureCacheRequest, ExecuteRequest, IndexRequest, KeyOrFilter, KeysOrFilter
from .cache_service_messages_v1_pb2 import MapListenerRequest as V1MapListenerRequest
from .cache_service_messages_v1_pb2 import NamedCacheRequest, NamedCacheRequestType, NamedCacheResponse
from .cache_service_messages_v1_pb2 import PutAllRequest as V1PutAllRequest
from .cache_service_messages_v1_pb2 import PutRequest as V1PutRequest
from .cache_service_messages_v1_pb2 import QueryRequest
from .cache_service_messages_v1_pb2 import ReplaceMappingRequest as V1ReplaceMappingRequest
from .common_messages_v1_pb2 import BinaryKeyAndValue, CollectionOfBytesValues, OptionalValue
from .comparator import Comparator
from .entry import MapEntry
from .extractor import ValueExtractor
from .filter import Filter, Filters, MapEventFilter
from .messages_pb2 import (
    AddIndexRequest,
    AggregateRequest,
    ClearRequest,
    ContainsKeyRequest,
    ContainsValueRequest,
    DestroyRequest,
    Entry,
    EntrySetRequest,
    GetAllRequest,
    GetRequest,
    InvokeAllRequest,
    InvokeRequest,
    IsEmptyRequest,
    KeySetRequest,
    MapListenerRequest,
    PageRequest,
    PutAllRequest,
    PutIfAbsentRequest,
    PutRequest,
    RemoveIndexRequest,
    RemoveMappingRequest,
    RemoveRequest,
    ReplaceMappingRequest,
    ReplaceRequest,
    SizeRequest,
    TruncateRequest,
    ValuesRequest,
)
from .processor import EntryProcessor
from .proxy_service_messages_v1_pb2 import InitRequest, ProxyRequest
from .serialization import Serializer

E = TypeVar("E")
K = TypeVar("K")
R = TypeVar("R")
T = TypeVar("T")
V = TypeVar("V")


def cur_time_millis() -> int:
    """
    :return: the current time, in millis, since epoch
    """
    return time.time_ns() // 1_000_000


def millis_format_date(millis: int) -> str:
    """
    Format the given time in millis to a readable format.

    :param millis: the millis time to format
    :return: the formatted date
    """
    dt = datetime.fromtimestamp(millis / 1000, timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")


class Dispatcher(ABC):
    def __init__(self, timeout: float):
        super().__init__()
        self._timeout: float = timeout

    @abstractmethod
    async def dispatch(self, stream_handler: Any) -> None:
        pass


class ResponseTransformer(ABC, Generic[T]):
    def __init__(self, serializer: Serializer):
        self._serializer = serializer

    @abstractmethod
    def transform(self, response: NamedCacheResponse) -> T:
        pass

    @property
    def serializer(self) -> Serializer:
        return self._serializer


class ScalarResultProducer(ABC, Generic[T]):
    @abstractmethod
    def result(self) -> T:
        pass


class KeyValueTransformer(ResponseTransformer[MapEntry[K, V]]):
    def __init__(self, serializer: Serializer):
        super().__init__(serializer)

    def transform(self, response: NamedCacheResponse) -> MapEntry[K, V]:
        from coherence import MapEntry

        binary_key_value = BinaryKeyAndValue()
        response.message.Unpack(binary_key_value)
        return MapEntry(
            self.serializer.deserialize(binary_key_value.key), self._serializer.deserialize(binary_key_value.value)
        )


class ValueTransformer(ResponseTransformer[V]):
    def __init__(self, serializer: Serializer):
        super().__init__(serializer)

    def transform(self, response: NamedCacheResponse) -> V:
        binary_key_value = BinaryKeyAndValue()
        response.message.Unpack(binary_key_value)
        return self.serializer.deserialize(binary_key_value.value)


class OptionalValueTransformer(ResponseTransformer[Optional[T]]):
    def __init__(self, serializer: Serializer):
        super().__init__(serializer)

    def transform(self, response: NamedCacheResponse) -> Optional[T]:
        optional_value = OptionalValue()
        response.message.Unpack(optional_value)
        if optional_value.present:
            return self.serializer.deserialize(optional_value.value)
        else:
            return None


class IntValueTransformer(ResponseTransformer[int]):
    def __init__(self, serializer: Serializer):
        super().__init__(serializer)

    def transform(self, response: NamedCacheResponse) -> int:
        value = Int32Value()
        response.message.Unpack(value)
        return value.value


class BoolValueTransformer(ResponseTransformer[bool]):
    def __init__(self, serializer: Serializer):
        super().__init__(serializer)

    def transform(self, response: NamedCacheResponse) -> bool:
        bool_value = BoolValue()
        response.message.Unpack(bool_value)
        return bool_value.value


class BytesValueTransformer(ResponseTransformer[Optional[T]]):
    def __init__(self, serializer: Serializer):
        super().__init__(serializer)

    def transform(self, response: NamedCacheResponse) -> Optional[T]:
        bytes_value = BytesValue()
        response.message.Unpack(bytes_value)
        result: T = self.serializer.deserialize(bytes_value.value)
        return result


class CookieTransformer(ResponseTransformer[bytes]):
    def transform(self, response: NamedCacheResponse) -> bytes:
        bytes_value = BytesValue()
        response.message.Unpack(bytes_value)
        return bytes_value.value


class CacheIdTransformer(ResponseTransformer[int]):

    def transform(self, response: NamedCacheResponse) -> int:
        return response.cacheId


class ResponseObserver(ABC):
    def __init__(self, request: ProxyRequest):
        if request is None:
            raise ValueError("Request cannot be None")

        self._request: ProxyRequest = request
        self._waiter: Event = Event()
        self._complete: bool = False
        self._error: Optional[Exception] = None

    @abstractmethod
    def _next(self, response: NamedCacheResponse) -> None:
        pass

    def _err(self, error: Exception) -> None:
        self._error = error
        self._done()

    def _done(self) -> None:
        self._complete = True
        self._waiter.set()

    @property
    def id(self) -> int:
        return self._request.id


class UnaryDispatcher(ResponseObserver, Dispatcher, ScalarResultProducer[T]):
    def __init__(self, timeout: float, request: ProxyRequest, transformer: Optional[ResponseTransformer[T]] = None):
        ResponseObserver.__init__(self, request)
        Dispatcher.__init__(self, timeout)
        self._waiter = Event()
        self._transformer = transformer
        self._result: T
        self._complete: bool = False

    def _next(self, response: NamedCacheResponse) -> None:
        if self._complete is True:
            return

        if self._transformer is not None:
            self._result = self._transformer.transform(response)

    async def dispatch(self, stream_handler: Any) -> None:
        from . import _TIMEOUT_CONTEXT_VAR

        assert self._complete is False

        stream_handler.register_observer(self)

        async def _dispatch_and_wait() -> None:
            await stream_handler.send_proxy_request(self._request)

            await self._waiter.wait()

            if self._error is not None:
                raise self._error

        try:
            await asyncio.wait_for(_dispatch_and_wait(), _TIMEOUT_CONTEXT_VAR.get(self._timeout))
        except Exception as e:
            stream_handler.deregister_observer(self)
            raise e

    def result(self) -> T:
        return self._result


class StreamingDispatcher(ResponseObserver, Dispatcher, AsyncIterator[T]):
    def __init__(self, timeout: float, request: ProxyRequest, transformer: ResponseTransformer[T]):
        ResponseObserver.__init__(self, request)
        Dispatcher.__init__(self, timeout)
        self._transformer = transformer
        self._stream_handler: Any
        self._deadline = Event()

    def _next(self, response: NamedCacheResponse) -> None:
        if self._complete is True:
            return

        self._result: T = self._transformer.transform(response)
        self._waiter.set()

    async def dispatch(self, stream_handler: Any) -> None:
        # noinspection PyAttributeOutsideInit
        self._stream_handler = stream_handler
        stream_handler.register_observer(self)

        # setup deadline handling for this call
        async def deadline() -> None:
            from . import _TIMEOUT_CONTEXT_VAR

            try:
                await stream_handler.send_proxy_request(self._request)

                if self._error is not None:
                    raise self._error

                await asyncio.wait_for(self._deadline.wait(), _TIMEOUT_CONTEXT_VAR.get(self._timeout))
            except Exception as e:
                stream_handler.deregister_observer(self)
                self._error = e
                self._waiter.set()  # raise error to the caller

        asyncio.get_running_loop().create_task(deadline())

    def __aiter__(self) -> AsyncIterator[T]:
        return self

    async def __anext__(self) -> T:
        await self._waiter.wait()
        if self._error is not None:
            raise self._error
        elif self._complete is True:
            self._deadline.set()
            raise StopAsyncIteration
        else:
            try:
                return self._result
            finally:
                self._waiter.clear()


class PagingDispatcher(ResponseObserver, Dispatcher, AsyncIterator[T]):
    def __init__(
        self,
        timeout: float,
        request: ProxyRequest,
        request_creator: Callable[[bytes], ProxyRequest],
        transformer: ResponseTransformer[T],
    ):
        ResponseObserver.__init__(self, request)
        Dispatcher.__init__(self, timeout)
        self._cookie_transformer: ResponseTransformer[Any] = CookieTransformer(transformer.serializer)
        self._transformer: ResponseTransformer[T] = transformer
        self._request_creator: Callable[[bytes], ProxyRequest] = request_creator
        self._first: bool = True
        self._cookie: bytes = bytes()
        self._exhausted: bool = False
        self._stream_handler: Any
        self._timeout: float = timeout
        self._in_progress: bool = False
        self._deadline = Event()

    def _next(self, response: NamedCacheResponse) -> None:
        if self._complete is True:
            return

        if self._first:
            # first response will have the cookie
            self._first = False
            self._cookie = self._cookie_transformer.transform(response)
            self._exhausted = self._cookie == b""
        else:
            self._result: T = self._transformer.transform(response)
            self._waiter.set()

    def _done(self) -> None:
        if self._exhausted:
            self._complete = True
            self._waiter.set()
        else:
            self._first = True
            self._request = self._request_creator(self._cookie)
            asyncio.create_task(self.dispatch(self._stream_handler))

    async def dispatch(self, stream_handler: Any) -> None:
        # noinspection PyAttributeOutsideInit
        self._stream_handler = stream_handler
        stream_handler.register_observer(self)

        if self._in_progress is False:
            self._in_progress = True

            # setup deadline handling for this call
            async def deadline() -> None:
                from . import _TIMEOUT_CONTEXT_VAR

                try:
                    await stream_handler.send_proxy_request(self._request)

                    if self._error is not None:
                        raise self._error

                    await asyncio.wait_for(self._deadline.wait(), _TIMEOUT_CONTEXT_VAR.get(self._timeout))
                except Exception as e:
                    stream_handler.deregister_observer(self)
                    self._error = e
                    self._waiter.set()  # raise error to the caller

            asyncio.get_running_loop().create_task(deadline())
        else:
            await stream_handler.send_proxy_request(self._request)

            if self._error is not None:
                stream_handler.deregister_observer(self)
                raise self._error

    def __aiter__(self) -> AsyncIterator[T]:
        return self

    async def __anext__(self) -> T:
        await self._waiter.wait()
        if self._error is not None:
            raise self._error
        elif self._complete is True:
            raise StopAsyncIteration
        else:
            try:
                return self._result
            finally:
                self._waiter.clear()


class RequestFactory:
    def __init__(self, cache_name: str, scope: str, serializer: Serializer) -> None:
        self._cache_name: str = cache_name
        self._scope: str = scope
        self._serializer: Serializer = serializer
        self.__uidPrefix: str = "-" + cache_name + "-" + str(time.time_ns())
        self.__next_request_id: int = 0
        self.__next_filter_id: int = 0

    @property
    def serializer(self) -> Serializer:
        return self._serializer

    def put_request(self, key: K, value: V, ttl: int = -1) -> PutRequest:
        p = PutRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format,
            key=self._serializer.serialize(key),
            value=self._serializer.serialize(value),
            ttl=ttl,
        )
        return p

    def get_request(self, key: K) -> GetRequest:
        g = GetRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format,
            key=self._serializer.serialize(key),
        )
        return g

    def get_all_request(self, keys: set[K]) -> GetAllRequest:
        if keys is None:
            raise ValueError("Must specify a set of keys")

        get_all: GetAllRequest = GetAllRequest(
            scope=self._scope, cache=self._cache_name, format=self._serializer.format
        )

        for key in keys:
            get_all.key.append(self._serializer.serialize(key))

        return get_all

    def put_if_absent_request(self, key: K, value: V, ttl: int = -1) -> PutIfAbsentRequest:
        p = PutIfAbsentRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format,
            key=self._serializer.serialize(key),
            value=self._serializer.serialize(value),
            ttl=ttl,
        )
        return p

    def put_all_request(self, map: dict[K, V]) -> PutAllRequest:
        entry_list = list()
        for key, value in map.items():
            k = self._serializer.serialize(key)
            v = self._serializer.serialize(value)
            e = Entry(key=k, value=v)
            entry_list.append(e)
        p = PutAllRequest(scope=self._scope, cache=self._cache_name, format=self._serializer.format, entry=entry_list)
        return p

    def clear_request(self) -> ClearRequest:
        r = ClearRequest(scope=self._scope, cache=self._cache_name)
        return r

    def destroy_request(self) -> DestroyRequest:
        r = DestroyRequest(scope=self._scope, cache=self._cache_name)
        return r

    def truncate_request(self) -> TruncateRequest:
        r = TruncateRequest(scope=self._scope, cache=self._cache_name)
        return r

    def remove_request(self, key: K) -> RemoveRequest:
        r = RemoveRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format,
            key=self._serializer.serialize(key),
        )
        return r

    def remove_mapping_request(self, key: K, value: V) -> RemoveMappingRequest:
        r = RemoveMappingRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format,
            key=self._serializer.serialize(key),
            value=self._serializer.serialize(value),
        )
        return r

    def replace_request(self, key: K, value: V) -> ReplaceRequest:
        r = ReplaceRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format,
            key=self._serializer.serialize(key),
            value=self._serializer.serialize(value),
        )
        return r

    def replace_mapping_request(self, key: K, old_value: V, new_value: V) -> ReplaceMappingRequest:
        r = ReplaceMappingRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format,
            key=self._serializer.serialize(key),
            previousValue=self._serializer.serialize(old_value),
            newValue=self._serializer.serialize(new_value),
        )
        return r

    def contains_key_request(self, key: K) -> ContainsKeyRequest:
        r = ContainsKeyRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format,
            key=self._serializer.serialize(key),
        )
        return r

    def contains_value_request(self, value: V) -> ContainsValueRequest:
        r = ContainsValueRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format,
            value=self._serializer.serialize(value),
        )
        return r

    def is_empty_request(self) -> IsEmptyRequest:
        r = IsEmptyRequest(scope=self._scope, cache=self._cache_name)
        return r

    def size_request(self) -> SizeRequest:
        r = SizeRequest(scope=self._scope, cache=self._cache_name)
        return r

    def invoke_request(self, key: K, processor: EntryProcessor[R]) -> InvokeRequest:
        r = InvokeRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format,
            processor=self._serializer.serialize(processor),
            key=self._serializer.serialize(key),
        )
        return r

    def invoke_all_request(
        self, processor: EntryProcessor[R], keys: Optional[set[K]] = None, filter: Optional[Filter] = None
    ) -> InvokeAllRequest:
        if keys is not None and filter is not None:
            raise ValueError("keys and filter are mutually exclusive")

        r = InvokeAllRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format,
            processor=self._serializer.serialize(processor),
        )

        if keys is not None:
            for key in keys:
                r.keys.append(self._serializer.serialize(key))
        else:
            r.filter = self._serializer.serialize(filter)

        return r

    def aggregate_request(
        self, aggregator: EntryAggregator[R], keys: Optional[set[K]] = None, filter: Optional[Filter] = None
    ) -> AggregateRequest:
        if keys is not None and filter is not None:
            raise ValueError("keys and filter are mutually exclusive")

        r: AggregateRequest = AggregateRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format,
            aggregator=self._serializer.serialize(aggregator),
        )

        if keys is not None:
            for key in keys:
                r.keys.append(self._serializer.serialize(key))
        if filter is not None:
            r.filter = self._serializer.serialize(filter)

        return r

    def values_request(self, filter: Optional[Filter] = None, comparator: Optional[Comparator] = None) -> ValuesRequest:
        if filter is None and comparator is not None:
            raise ValueError("Filter cannot be None")

        r: ValuesRequest = ValuesRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format,
        )

        if filter is not None:
            r.filter = self._serializer.serialize(filter)

        if comparator is not None:
            r.comparator = self._serializer.serialize(comparator)

        return r

    def keys_request(self, filter: Optional[Filter] = None) -> KeySetRequest:
        r: KeySetRequest = KeySetRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format,
        )

        if filter is not None:
            r.filter = self._serializer.serialize(filter)

        return r

    def entries_request(
        self, filter: Optional[Filter] = None, comparator: Optional[Comparator] = None
    ) -> EntrySetRequest:
        if filter is None and comparator is not None:
            raise ValueError("Filter cannot be None")

        r: EntrySetRequest = EntrySetRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format,
        )

        if filter is not None:
            r.filter = self._serializer.serialize(filter)

        if comparator is not None:
            r.comparator = self._serializer.serialize(comparator)

        return r

    def page_request(self, cookie: bytes) -> PageRequest:
        """
        Creates a gRPC PageRequest.

        :param cookie: the cookie used for paging
        :return: a new PageRequest
        """

        r: PageRequest = PageRequest(
            scope=self._scope, cache=self._cache_name, format=self._serializer.format, cookie=cookie
        )

        return r

    def map_listener_request(
        self, subscribe: bool, lite: bool = False, *, key: Optional[K] = None, filter: Optional[Filter] = None
    ) -> MapListenerRequest:
        """Creates a gRPC generated MapListenerRequest"""

        if key is None and filter is None:
            raise AssertionError("Must specify a key or a filter")

        request: MapListenerRequest = MapListenerRequest(
            cache=self._cache_name, scope=self._scope, format=self._serializer.format
        )

        request.lite = lite
        request.subscribe = subscribe
        request.uid = self.__generate_next_request_id("key" if key is not None else "filter")
        request.trigger = bytes()
        request.priming = False

        if key is not None:  # registering a key listener
            # noinspection PyUnresolvedReferences
            request.type = MapListenerRequest.RequestType.KEY
            request.key = self._serializer.serialize(key)
        else:  # registering a Filter listener
            # noinspection PyUnresolvedReferences
            request.type = MapListenerRequest.RequestType.FILTER
            self.__next_filter_id += 1
            request.filterId = self.__next_filter_id
            filter_local: Filter = filter if filter is not None else Filters.always()
            if not isinstance(filter_local, MapEventFilter):
                # noinspection PyUnresolvedReferences
                filter_local = MapEventFilter.from_filter(filter_local)

            request.filter = self._serializer.serialize(filter_local)

        return request

    def map_event_subscribe(self) -> MapListenerRequest:
        request: MapListenerRequest = MapListenerRequest(
            cache=self._cache_name, scope=self._scope, format=self._serializer.format
        )
        request.uid = self.__generate_next_request_id("init")
        request.subscribe = True
        # noinspection PyUnresolvedReferences
        request.type = MapListenerRequest.RequestType.INIT

        return request

    def __generate_next_request_id(self, prefix: str) -> str:
        """Generates a prefix map-specific prefix when starting a MapEvent gRPC stream."""
        self.__next_request_id += 1
        return prefix + self.__uidPrefix + str(self.__next_request_id)

    def add_index_request(
        self, extractor: ValueExtractor[T, E], ordered: bool = False, comparator: Optional[Comparator] = None
    ) -> AddIndexRequest:
        r = AddIndexRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format,
            extractor=self._serializer.serialize(extractor),
        )
        r.sorted = ordered

        if comparator is not None:
            r.comparator = self._serializer.serialize(comparator)

        return r

    def remove_index_request(self, extractor: ValueExtractor[T, E]) -> RemoveIndexRequest:
        r = RemoveIndexRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format,
            extractor=self._serializer.serialize(extractor),
        )

        return r


class RequestIdGenerator:
    _generator = None

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counter = 0

    @classmethod
    def generator(cls) -> RequestIdGenerator:
        if RequestIdGenerator._generator is None:
            RequestIdGenerator._generator = RequestIdGenerator()
        return RequestIdGenerator._generator

    @classmethod
    def next(cls) -> int:
        generator = cls.generator()
        with generator._lock:
            if generator._counter == sys.maxsize:
                generator._counter = 0
            else:
                generator._counter += 1
            return generator._counter


class RequestFactoryV1:

    def __init__(
        self, cache_name: str, cache_id: int, scope: str, serializer: Serializer, timeout: Callable[[], float]
    ) -> None:
        self._cache_name: str = cache_name
        self._cache_id: int = cache_id
        self._scope: str = scope
        self._timeout: Callable[[], float] = timeout
        self._serializer: Serializer = serializer

    @property
    def cache_id(self) -> int:
        return self._cache_id

    @cache_id.setter
    def cache_id(self, value: int) -> None:
        self._cache_id = value

    @property
    def request_timeout(self) -> float:
        return self._timeout()

    def _create_named_cache_request(self, request: Any, request_type: NamedCacheRequestType) -> NamedCacheRequest:
        any_cache_request = GrpcAny()
        any_cache_request.Pack(request)

        return NamedCacheRequest(
            type=request_type,
            cacheId=self.cache_id,
            message=any_cache_request,
        )

    def create_proxy_request(self, named_cache_request: NamedCacheRequest) -> ProxyRequest:
        any_named_cache_request = GrpcAny()
        any_named_cache_request.Pack(named_cache_request)
        req_id = RequestIdGenerator.next()
        proxy_request = ProxyRequest(
            id=req_id,
            message=any_named_cache_request,
        )
        return proxy_request

    @staticmethod
    def init_sub_channel(
        scope: str = "",
        serialization_format: str = "json",
        protocol: str = "CacheService",
        protocol_version: int = 1,
        supported_protocol_version: int = 1,
        heartbeat: int = 0,
    ) -> ProxyRequest:
        init_request = InitRequest(
            scope=scope,
            format=serialization_format,
            protocol=protocol,
            protocolVersion=protocol_version,
            supportedProtocolVersion=supported_protocol_version,
            heartbeat=heartbeat,
        )

        return ProxyRequest(id=2, init=init_request)

    def ensure_request(self, cache_name: str) -> UnaryDispatcher[int]:
        cache_request = EnsureCacheRequest(cache=cache_name)

        any_cache_request = GrpcAny()
        any_cache_request.Pack(cache_request)

        named_cache_request = NamedCacheRequest(
            type=NamedCacheRequestType.EnsureCache,
            message=any_cache_request,
        )
        return UnaryDispatcher(
            self.request_timeout, self.create_proxy_request(named_cache_request), CacheIdTransformer(self._serializer)
        )

    def put_request(self, key: K, value: V, ttl: int = 0) -> UnaryDispatcher[Optional[V]]:
        request: NamedCacheRequest = self._create_named_cache_request(
            V1PutRequest(
                key=self._serializer.serialize(key),  # Serialized key
                value=self._serializer.serialize(value),  # Serialized value
                ttl=ttl,
            ),
            NamedCacheRequestType.Put,
        )

        return UnaryDispatcher(
            self.request_timeout, self.create_proxy_request(request), OptionalValueTransformer(self._serializer)
        )

    def get_request(self, key: K) -> UnaryDispatcher[Optional[V]]:
        request: NamedCacheRequest = self._create_named_cache_request(
            BytesValue(value=self._serializer.serialize(key)), NamedCacheRequestType.Get
        )

        return UnaryDispatcher(
            self.request_timeout, self.create_proxy_request(request), OptionalValueTransformer(self._serializer)
        )

    def get_all_request(self, keys: set[K]) -> StreamingDispatcher[MapEntry[K, V]]:
        if keys is None:
            raise ValueError("Must specify a set of keys")

        named_cache_request: NamedCacheRequest = self._create_named_cache_request(
            CollectionOfBytesValues(
                values=list(self._serializer.serialize(k) for k in keys),
            ),
            NamedCacheRequestType.GetAll,
        )

        return StreamingDispatcher(
            self.request_timeout, self.create_proxy_request(named_cache_request), KeyValueTransformer(self._serializer)
        )

    def put_if_absent_request(self, key: K, value: V, ttl: int = 0) -> UnaryDispatcher[Optional[V]]:
        request: NamedCacheRequest = self._create_named_cache_request(
            V1PutRequest(
                key=self._serializer.serialize(key),  # Serialized key
                value=self._serializer.serialize(value),  # Serialized value
                ttl=ttl,
            ),
            NamedCacheRequestType.PutIfAbsent,
        )

        return UnaryDispatcher(
            self.request_timeout, self.create_proxy_request(request), BytesValueTransformer(self._serializer)
        )

    def put_all_request(self, kv_map: dict[K, V], ttl: Optional[int] = 0) -> Dispatcher:
        request: NamedCacheRequest = self._create_named_cache_request(
            V1PutAllRequest(
                entries=list(
                    BinaryKeyAndValue(key=self._serializer.serialize(k), value=self._serializer.serialize(v))
                    for k, v in kv_map.items()
                ),
                ttl=ttl,
            ),
            NamedCacheRequestType.PutAll,
        )

        return UnaryDispatcher(self.request_timeout, self.create_proxy_request(request))

    def clear_request(self) -> Dispatcher:
        named_cache_request = NamedCacheRequest(
            type=NamedCacheRequestType.Clear,
            cacheId=self.cache_id,
        )
        return UnaryDispatcher(self.request_timeout, self.create_proxy_request(named_cache_request))

    def destroy_request(self) -> Dispatcher:
        named_cache_request: NamedCacheRequest = NamedCacheRequest(
            type=NamedCacheRequestType.Destroy,
            cacheId=self.cache_id,
        )

        return UnaryDispatcher(self.request_timeout, self.create_proxy_request(named_cache_request))

    def truncate_request(self) -> Dispatcher:
        named_cache_request: NamedCacheRequest = NamedCacheRequest(
            type=NamedCacheRequestType.Truncate,
            cacheId=self.cache_id,
        )
        return UnaryDispatcher(self.request_timeout, self.create_proxy_request(named_cache_request))

    def remove_request(self, key: K) -> UnaryDispatcher[Optional[V]]:
        named_cache_request: NamedCacheRequest = self._create_named_cache_request(
            BytesValue(value=self._serializer.serialize(key)), NamedCacheRequestType.Remove
        )

        return UnaryDispatcher(
            self.request_timeout,
            self.create_proxy_request(named_cache_request),
            BytesValueTransformer(self._serializer),
        )

    def remove_mapping_request(self, key: K, value: V) -> UnaryDispatcher[bool]:
        named_cache_request: NamedCacheRequest = self._create_named_cache_request(
            BinaryKeyAndValue(key=self._serializer.serialize(key), value=self._serializer.serialize(value)),
            NamedCacheRequestType.RemoveMapping,
        )

        return UnaryDispatcher(
            self.request_timeout, self.create_proxy_request(named_cache_request), BoolValueTransformer(self._serializer)
        )

    def replace_request(self, key: K, value: V) -> UnaryDispatcher[Optional[V]]:
        named_cache_request: NamedCacheRequest = self._create_named_cache_request(
            BinaryKeyAndValue(key=self._serializer.serialize(key), value=self._serializer.serialize(value)),
            NamedCacheRequestType.Replace,
        )

        return UnaryDispatcher(
            self.request_timeout,
            self.create_proxy_request(named_cache_request),
            BytesValueTransformer(self._serializer),
        )

    def replace_mapping_request(self, key: K, old_value: V, new_value: V) -> UnaryDispatcher[bool]:
        named_cache_request: NamedCacheRequest = self._create_named_cache_request(
            V1ReplaceMappingRequest(
                key=self._serializer.serialize(key),
                previousValue=self._serializer.serialize(old_value),
                newValue=self._serializer.serialize(new_value),
            ),
            NamedCacheRequestType.ReplaceMapping,
        )

        return UnaryDispatcher(
            self.request_timeout, self.create_proxy_request(named_cache_request), BoolValueTransformer(self._serializer)
        )

    def contains_key_request(self, key: K) -> UnaryDispatcher[bool]:
        named_cache_request = self._create_named_cache_request(
            BytesValue(value=self._serializer.serialize(key)), NamedCacheRequestType.ContainsKey
        )

        return UnaryDispatcher(
            self.request_timeout, self.create_proxy_request(named_cache_request), BoolValueTransformer(self._serializer)
        )

    def contains_value_request(self, value: V) -> UnaryDispatcher[bool]:
        named_cache_request = self._create_named_cache_request(
            BytesValue(value=self._serializer.serialize(value)), NamedCacheRequestType.ContainsValue
        )

        return UnaryDispatcher(
            self.request_timeout, self.create_proxy_request(named_cache_request), BoolValueTransformer(self._serializer)
        )

    def is_empty_request(self) -> UnaryDispatcher[bool]:
        named_cache_request = NamedCacheRequest(
            type=NamedCacheRequestType.IsEmpty,
            cacheId=self.cache_id,
        )

        return UnaryDispatcher(
            self.request_timeout, self.create_proxy_request(named_cache_request), BoolValueTransformer(self._serializer)
        )

    def size_request(self) -> UnaryDispatcher[int]:
        named_cache_request = NamedCacheRequest(
            type=NamedCacheRequestType.Size,
            cacheId=self.cache_id,
        )

        return UnaryDispatcher(
            self.request_timeout, self.create_proxy_request(named_cache_request), IntValueTransformer(self._serializer)
        )

    def invoke_request(self, key: K, processor: EntryProcessor[R]) -> UnaryDispatcher[Optional[R]]:
        named_cache_request: NamedCacheRequest = self._create_named_cache_request(
            ExecuteRequest(
                agent=self._serializer.serialize(processor),
                keys=KeysOrFilter(
                    key=self._serializer.serialize(key),
                ),
            ),
            NamedCacheRequestType.Invoke,
        )

        return UnaryDispatcher(
            self.request_timeout, self.create_proxy_request(named_cache_request), ValueTransformer(self._serializer)
        )

    def invoke_all_request(
        self, processor: EntryProcessor[R], keys: Optional[set[K]] = None, filter: Optional[Filter] = None
    ) -> StreamingDispatcher[MapEntry[K, R]]:
        if keys is not None and filter is not None:
            raise ValueError("keys and filter are mutually exclusive")

        if keys is not None:
            cache_request = ExecuteRequest(
                agent=self._serializer.serialize(processor),
                keys=KeysOrFilter(
                    keys=CollectionOfBytesValues(
                        values=list(self._serializer.serialize(key) for key in keys),
                    ),
                ),
            )
        elif filter is not None:
            cache_request = ExecuteRequest(
                agent=self._serializer.serialize(processor),
                keys=KeysOrFilter(
                    filter=self._serializer.serialize(filter),
                ),
            )
        else:
            cache_request = ExecuteRequest(
                agent=self._serializer.serialize(processor),
            )

        named_cache_request: NamedCacheRequest = self._create_named_cache_request(
            cache_request, NamedCacheRequestType.Invoke
        )

        return StreamingDispatcher(
            self.request_timeout, self.create_proxy_request(named_cache_request), KeyValueTransformer(self._serializer)
        )

    def aggregate_request(
        self, aggregator: EntryAggregator[R], keys: Optional[set[K]] = None, filter: Optional[Filter] = None
    ) -> UnaryDispatcher[Optional[R]]:
        if keys is not None and filter is not None:
            raise ValueError("keys and filter are mutually exclusive")

        if keys is not None:
            cache_request = ExecuteRequest(
                agent=self._serializer.serialize(aggregator),
                keys=KeysOrFilter(
                    keys=CollectionOfBytesValues(
                        values=list(self._serializer.serialize(key) for key in keys),
                    ),
                ),
            )
        elif filter is not None:
            cache_request = ExecuteRequest(
                agent=self._serializer.serialize(aggregator),
                keys=KeysOrFilter(
                    filter=self._serializer.serialize(filter),
                ),
            )
        else:
            cache_request = ExecuteRequest(
                agent=self._serializer.serialize(aggregator),
            )

        named_cache_request: NamedCacheRequest = self._create_named_cache_request(
            cache_request, NamedCacheRequestType.Aggregate
        )
        return UnaryDispatcher(
            self.request_timeout,
            self.create_proxy_request(named_cache_request),
            BytesValueTransformer(self._serializer),
        )

    def values_request(
        self, filter: Optional[Filter] = None, comparator: Optional[Comparator] = None
    ) -> StreamingDispatcher[V]:
        if filter is None and comparator is not None:
            raise ValueError("Filter cannot be None")

        if filter is not None:
            query_request = QueryRequest(filter=self._serializer.serialize(filter))
        elif comparator is not None:
            query_request = QueryRequest(comparator=self._serializer.serialize(comparator))
        else:
            query_request = QueryRequest()

        named_cache_request: NamedCacheRequest = self._create_named_cache_request(
            query_request, NamedCacheRequestType.QueryValues
        )

        return StreamingDispatcher(
            self.request_timeout,
            self.create_proxy_request(named_cache_request),
            BytesValueTransformer(self._serializer),  # type: ignore
        )

    def keys_request(self, filter: Optional[Filter] = None) -> StreamingDispatcher[K]:

        if filter is not None:
            query_request = QueryRequest(filter=self._serializer.serialize(filter))
        else:
            query_request = QueryRequest()

        named_cache_request: NamedCacheRequest = self._create_named_cache_request(
            query_request, NamedCacheRequestType.QueryKeys
        )

        return StreamingDispatcher(
            self.request_timeout,
            self.create_proxy_request(named_cache_request),
            BytesValueTransformer(self._serializer),  # type: ignore
        )

    def entries_request(
        self, filter: Optional[Filter] = None, comparator: Optional[Comparator] = None
    ) -> StreamingDispatcher[MapEntry[K, V]]:
        if filter is None and comparator is not None:
            raise ValueError("Filter cannot be None")

        if filter is not None:
            query_request = QueryRequest(filter=self._serializer.serialize(filter))
        elif comparator is not None:
            query_request = QueryRequest(comparator=self._serializer.serialize(comparator))
        else:
            query_request = QueryRequest()

        named_cache_request: NamedCacheRequest = self._create_named_cache_request(
            query_request, NamedCacheRequestType.QueryEntries
        )

        return StreamingDispatcher(
            self.request_timeout, self.create_proxy_request(named_cache_request), KeyValueTransformer(self._serializer)
        )

    def page_request(self, keys_only: bool = False, values_only: bool = False) -> PagingDispatcher[T]:
        """
        Creates a gRPC PageRequest.

        :param keys_only: flag indicating interest in only keys
        :param values_only: flag indicating interest in only values
        :return: a new PageRequest
        """
        if keys_only and values_only:
            raise ValueError("keys_only and values_only cannot be True at the same time")

        if keys_only:
            return PagingDispatcher(
                self.request_timeout,
                self._page_of_keys_creator(None),
                self._page_of_keys_creator,
                BytesValueTransformer(self._serializer),  # type: ignore
            )
        elif values_only:
            return PagingDispatcher(
                self.request_timeout,
                self._page_of_entries_creator(None),
                self._page_of_entries_creator,
                ValueTransformer(self._serializer),
            )
        else:
            return PagingDispatcher(
                self.request_timeout,
                self._page_of_entries_creator(None),
                self._page_of_entries_creator,
                KeyValueTransformer(self._serializer),  # type: ignore
            )

    def _page_of_keys_creator(self, cookie: Optional[bytes]) -> ProxyRequest:
        if cookie is None:
            cookie_bytes = BytesValue()
        else:
            cookie_bytes = BytesValue(value=cookie)

        return self.create_proxy_request(
            self._create_named_cache_request(cookie_bytes, NamedCacheRequestType.PageOfKeys)
        )

    def _page_of_entries_creator(self, cookie: Optional[bytes]) -> ProxyRequest:
        if cookie is None:
            cookie_bytes = BytesValue()
        else:
            cookie_bytes = BytesValue(value=cookie)

        return self.create_proxy_request(
            self._create_named_cache_request(cookie_bytes, NamedCacheRequestType.PageOfEntries)
        )

    def map_listener_request(
        self,
        subscribe: bool,
        lite: bool = False,
        sync: bool = False,
        priming: bool = False,
        *,
        key: Optional[K] = None,
        filter: Optional[Filter] = None,
        filter_id: int = -1,
    ) -> Tuple[UnaryDispatcher[Any], ProxyRequest, int]:
        """Creates a gRPC generated MapListenerRequest"""

        if key is None and filter is None:
            raise AssertionError("Must specify a key or a filter")

        if key is None:  # registering a Filter listener
            filter_local: Filter = filter if filter is not None else Filters.always()
            if not isinstance(filter_local, MapEventFilter):
                # noinspection PyUnresolvedReferences
                filter_local = MapEventFilter.from_filter(filter_local)
            listener_request: V1MapListenerRequest = V1MapListenerRequest(
                subscribe=subscribe,
                lite=lite,
                synchronous=sync,
                priming=priming,
                filterId=RequestIdGenerator.next() if filter_id == -1 else filter_id,
                keyOrFilter=KeyOrFilter(filter=self._serializer.serialize(filter_local)),
            )
        else:  # registering a key listener
            listener_request = V1MapListenerRequest(
                subscribe=subscribe,
                lite=lite,
                synchronous=sync,
                priming=priming,
                keyOrFilter=KeyOrFilter(key=self._serializer.serialize(key)),
            )

        named_cache_request: NamedCacheRequest = self._create_named_cache_request(
            listener_request, NamedCacheRequestType.MapListener
        )
        proxy_request: ProxyRequest = self.create_proxy_request(named_cache_request)

        return (
            UnaryDispatcher(self.request_timeout, proxy_request),
            proxy_request,
            listener_request.filterId,
        )

    def add_index_request(
        self, extractor: ValueExtractor[T, E], ordered: bool = False, comparator: Optional[Comparator] = None
    ) -> Dispatcher:
        if comparator is None:
            named_cache_request: NamedCacheRequest = self._create_named_cache_request(
                IndexRequest(add=True, extractor=self._serializer.serialize(extractor), sorted=ordered),
                NamedCacheRequestType.Index,
            )
        else:
            named_cache_request = self._create_named_cache_request(
                IndexRequest(
                    add=True,
                    extractor=self._serializer.serialize(extractor),
                    sorted=ordered,
                    comparator=self._serializer.serialize(extractor),
                ),
                NamedCacheRequestType.Index,
            )

        return UnaryDispatcher(self.request_timeout, self.create_proxy_request(named_cache_request))

    def remove_index_request(self, extractor: ValueExtractor[T, E]) -> Dispatcher:
        named_cache_request: NamedCacheRequest = self._create_named_cache_request(
            IndexRequest(
                add=False,
                extractor=self._serializer.serialize(extractor),
            ),
            NamedCacheRequestType.Index,
        )

        return UnaryDispatcher(self.request_timeout, self.create_proxy_request(named_cache_request))
