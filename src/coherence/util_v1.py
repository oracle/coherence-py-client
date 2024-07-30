# Copyright (c) 2022, 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

import asyncio
import logging
import sys
import threading
import time
from asyncio import Event
from typing import Optional, TypeVar

import grpc
from google.protobuf.json_format import MessageToJson
from requests import Response

from . import cache_service_messages_v1_pb2, proxy_service_messages_v1_pb2,common_messages_v1_pb2
from .aggregator import EntryAggregator
from .comparator import Comparator
from .extractor import ValueExtractor
from .filter import Filter, Filters, MapEventFilter
from .messages_pb2 import (  # type: ignore
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
from .serialization import Serializer
from google.protobuf.any_pb2 import Any
from google.protobuf.wrappers_pb2 import BytesValue

E = TypeVar("E")
K = TypeVar("K")
R = TypeVar("R")
T = TypeVar("T")
V = TypeVar("V")

COH_LOG = logging.getLogger("coherence")


class Request_ID_Generator:
    _generator = None

    def __init__(self):
        self._lock = threading.Lock()
        self._counter = 0

    @classmethod
    def generator(cls):
        if Request_ID_Generator._generator is None:
            Request_ID_Generator._generator = Request_ID_Generator()
        return Request_ID_Generator._generator

    @classmethod
    def get_next_id(cls):
        generator = cls.generator()
        with generator._lock:
            if generator._counter == sys.maxsize:
                generator._counter = 0
            else:
                generator._counter += 1
            return generator._counter


class RequestFactory_v1:

    def __init__(self, cache_name: str, cache_id: int, session: Session, serializer: Serializer) -> None:
        self._cache_name = cache_name
        self._cache_id = cache_id
        self._session = session
        self._scope: str = session.scope
        self._serializer: Serializer = serializer
        # self.__uidPrefix: str = "-" + cache_name + "-" + str(time.time_ns())
        # self.__next_request_id: int = 0
        # self.__next_filter_id: int = 0

    @property
    def cache_id(self):
        return self._cache_id

    @cache_id.setter
    def cache_id(self, value):
        self._cache_id = value

    def get_serializer(self) -> Serializer:
        return self._serializer

    def create_proxy_request(self, named_cache_request:
                    cache_service_messages_v1_pb2.NamedCacheRequest) -> proxy_service_messages_v1_pb2.ProxyRequest:
        any_named_cache_request = Any()
        any_named_cache_request.Pack(named_cache_request)
        req_id = Request_ID_Generator.get_next_id()
        proxy_request = proxy_service_messages_v1_pb2.ProxyRequest(
            id=req_id,
            message=any_named_cache_request,
        )
        # self._session._request_id_map[req_id] = named_cache_request
        return proxy_request

    def ensure_request(self, cache_name: str) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        ensure_cache_request = cache_service_messages_v1_pb2.EnsureCacheRequest(
            cache=cache_name
        )

        any_ensure_cache_request = Any()
        any_ensure_cache_request.Pack(ensure_cache_request)

        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.EnsureCache,
            message=any_ensure_cache_request,
        )
        return named_cache_request

    def put_request(self, key: K, value: V, ttl: int = -1) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        put_request = cache_service_messages_v1_pb2.PutRequest(
            key=self._serializer.serialize(key),     # Serialized key
            value=self._serializer.serialize(value), # Serialized value
            ttl=ttl
        )

        any_put_request = Any()
        any_put_request.Pack(put_request)

        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.Put,
            cacheId=self.cache_id,
            message=any_put_request,
        )

        return named_cache_request

    def get_request(self, key: K) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        get_request = BytesValue(value=self._serializer.serialize(key))

        any_get_request = Any()
        any_get_request.Pack(get_request)

        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.Get,
            cacheId=self.cache_id,
            message=any_get_request,
        )

        return named_cache_request

    def get_all_request(self, keys: set[K]) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        if keys is None:
            raise ValueError("Must specify a set of keys")

        l = list()
        for k in keys:
            l.append(self._serializer.serialize(k))
        get_all_request = common_messages_v1_pb2.CollectionOfBytesValues(
            values=l,
        )

        any_request = Any()
        any_request.Pack(get_all_request)

        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.GetAll,
            cacheId=self.cache_id,
            message=any_request,
        )

        return named_cache_request

    def put_if_absent_request(self, key: K, value: V, ttl: int = -1) -> PutIfAbsentRequest:
        put_request = cache_service_messages_v1_pb2.PutRequest(
            key=self._serializer.serialize(key),     # Serialized key
            value=self._serializer.serialize(value), # Serialized value
            ttl=ttl
        )

        any_put_request = Any()
        any_put_request.Pack(put_request)

        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.PutIfAbsent,
            cacheId=self.cache_id,
            message=any_put_request,
        )

        return named_cache_request

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
        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.Clear,
            cacheId=self.cache_id,
        )
        return named_cache_request

    def destroy_request(self) -> DestroyRequest:
        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.Destroy,
            cacheId=self.cache_id,
        )
        return named_cache_request

    def truncate_request(self) -> TruncateRequest:
        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.Truncate,
            cacheId=self.cache_id,
        )
        return named_cache_request

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
            request.type = MapListenerRequest.RequestType.KEY
            request.key = self._serializer.serialize(key)
        else:  # registering a Filter listener
            request.type = MapListenerRequest.RequestType.FILTER
            self.__next_filter_id += 1
            request.filterId = self.__next_filter_id
            filter_local: Filter = filter if filter is not None else Filters.always()
            if not isinstance(filter_local, MapEventFilter):
                filter_local = MapEventFilter.from_filter(filter_local)

            request.filter = self._serializer.serialize(filter_local)

        return request

    def map_event_subscribe(self) -> MapListenerRequest:
        request: MapListenerRequest = MapListenerRequest(
            cache=self._cache_name, scope=self._scope, format=self._serializer.format
        )
        request.uid = self.__generate_next_request_id("init")
        request.subscribe = True
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


class StreamHandler:
    theStreamHandler = None

    def __init__(self, session: Session, stream: grpc.aio._call.StreamStreamCall):
        self._session: Session = session
        self._stream: grpc.aio._call.StreamStreamCall = stream
        self._request_id_to_event_map = dict()
        self._request_id_request_map = dict()
        self.result_available = Event()
        self.result_available.clear()
        self.response_result = None
        self.response_result_collection = list()
        asyncio.create_task(self.handle_response())

    @property
    def session(self) -> Session:
        return self._session

    @property
    def stream(self) -> grpc.aio._call.StreamStreamCall:
        return self._stream

    @classmethod
    def getStreamHandler(cls, session: Session, stream: grpc.aio._call.StreamStreamCall):
        if cls.theStreamHandler is None:
            cls.theStreamHandler = StreamHandler(session, stream)
            return cls.theStreamHandler
        else:
            return cls.theStreamHandler

    async def handle_response(self):
        COH_LOG.setLevel(logging.DEBUG)
        while not self.session.closed:
            await asyncio.sleep(0)
            response = await self.stream.read()
            response_id = response.id
            COH_LOG.debug(f"response_id: {response_id}")
            if response_id == 0 :
                self.handle_zero_id_response(response)
            else:
                if response.HasField("message"):
                    req_type = self._request_id_request_map[response_id].type
                    if req_type == cache_service_messages_v1_pb2.NamedCacheRequestType.EnsureCache:
                        named_cache_response = cache_service_messages_v1_pb2.NamedCacheResponse()
                        response.message.Unpack(named_cache_response)
                        # COH_LOG.info(f"cache_id: {named_cache_response.cacheId}")
                        self.response_result = named_cache_response
                    elif req_type == cache_service_messages_v1_pb2.NamedCacheRequestType.Put:
                        named_cache_response = cache_service_messages_v1_pb2.NamedCacheResponse()
                        response.message.Unpack(named_cache_response)
                        # COH_LOG.info("PUT request successful. Response:")
                        self.response_result = named_cache_response
                    elif req_type == cache_service_messages_v1_pb2.NamedCacheRequestType.PutIfAbsent:
                        named_cache_response = cache_service_messages_v1_pb2.NamedCacheResponse()
                        response.message.Unpack(named_cache_response)
                        # COH_LOG.info("PUT request successful. Response:")
                        self.response_result = named_cache_response
                    elif req_type == cache_service_messages_v1_pb2.NamedCacheRequestType.Get:
                        named_cache_response = cache_service_messages_v1_pb2.NamedCacheResponse()
                        response.message.Unpack(named_cache_response)
                        # COH_LOG.info("GET request successful. Response:")
                        self.response_result = named_cache_response
                    elif req_type == cache_service_messages_v1_pb2.NamedCacheRequestType.GetAll:
                        named_cache_response = cache_service_messages_v1_pb2.NamedCacheResponse()
                        response.message.Unpack(named_cache_response)
                        # COH_LOG.info("GET request successful. Response:")
                        self.response_result_collection.append(named_cache_response)
                    else:
                        pass
                elif response.HasField("init"):
                    self._request_id_to_event_map.pop(response_id)
                    print("InitRequest request completed.")
                    self.result_available.set()
                elif response.HasField("error"):
                    error_message = response.error
                    print(f"EnsureCache request failed with error: {error_message}")
                    return
                elif response.HasField("complete"):
                    # self.session.request_id_map.pop(response_id)
                    # COH_LOG.info("Complete response received successfully.")
                    self._request_id_to_event_map[response_id].set()

    async def get_response(self, response_id: int):
        await self._request_id_to_event_map[response_id].wait()
        result = self.response_result
        self.response_result = None
        self._request_id_to_event_map[response_id].clear()
        self._request_id_to_event_map.pop(response_id)
        self._request_id_request_map.pop(response_id)
        return result

    async def get_response_collection(self, response_id: int):
        await self._request_id_to_event_map[response_id].wait()
        result = self.response_result_collection
        self.response_result_collection = list()
        self._request_id_to_event_map[response_id].clear()
        self._request_id_to_event_map.pop(response_id)
        self._request_id_request_map.pop(response_id)
        return result

    async def write_request(self, proxy_request: proxy_service_messages_v1_pb2.ProxyRequest,
                            request_id: int,
                            request: cache_service_messages_v1_pb2.NamedCacheRequest):
        self._request_id_to_event_map[request_id] = Event()
        self._request_id_to_event_map[request_id].clear()
        self._request_id_request_map[request_id] = request
        await self._stream.write(proxy_request)

    def handle_zero_id_response(self, response):
        if response.HasField("message"):
            named_cache_response = cache_service_messages_v1_pb2.NamedCacheResponse()
            response.message.Unpack(named_cache_response)
            type = named_cache_response.type
            cache_id = named_cache_response.cacheId
            if type == cache_service_messages_v1_pb2.ResponseType.Message:
                pass
            elif type == cache_service_messages_v1_pb2.ResponseType.MapEvent:
                # Handle MapEvent Response
                COH_LOG.debug("MapEvent Response type received")
                response_json = MessageToJson(named_cache_response)
                COH_LOG.debug(response_json)
                pass
            elif type == cache_service_messages_v1_pb2.ResponseType.Destroyed:
                # Handle Destroyed Response
                COH_LOG.debug("Destroyed Response type received")
                response_json = MessageToJson(named_cache_response)
                COH_LOG.debug(response_json)
                pass
            elif type == cache_service_messages_v1_pb2.ResponseType.Truncated:
                # Handle Truncated Response
                COH_LOG.debug("Truncated Response type received")
                response_json = MessageToJson(named_cache_response)
                COH_LOG.debug(response_json)
            else:
                pass
