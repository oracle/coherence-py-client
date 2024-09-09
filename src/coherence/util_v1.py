# Copyright (c) 2022, 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

import logging
import sys
import threading
from typing import Optional, TypeVar

from google.protobuf.any_pb2 import Any as GrpcAny  # type: ignore
from google.protobuf.wrappers_pb2 import BytesValue  # type: ignore

from .aggregator import EntryAggregator
from .cache_service_messages_v1_pb2 import (
    EnsureCacheRequest,
    ExecuteRequest,
    IndexRequest,
    KeysOrFilter,
    NamedCacheRequest,
    NamedCacheRequestType,
    PutAllRequest,
    PutRequest,
    QueryRequest,
    ReplaceMappingRequest,
)
from .common_messages_v1_pb2 import BinaryKeyAndValue, CollectionOfBytesValues
from .comparator import Comparator
from .extractor import ValueExtractor
from .filter import Filter, Filters, MapEventFilter
from .messages_pb2 import MapListenerRequest, PageRequest
from .processor import EntryProcessor
from .proxy_service_messages_v1_pb2 import ProxyRequest
from .serialization import Serializer

E = TypeVar("E")
K = TypeVar("K")
R = TypeVar("R")
T = TypeVar("T")
V = TypeVar("V")

COH_LOG = logging.getLogger("coherence")


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

    def __init__(self, cache_name: str, cache_id: int, scope: str, serializer: Serializer) -> None:
        self._cache_name: str = cache_name
        self._cache_id: int = cache_id
        self._scope: str = scope
        self._serializer: Serializer = serializer
        # self.__uidPrefix: str = "-" + cache_name + "-" + str(time.time_ns())
        # self.__next_request_id: int = 0
        # self.__next_filter_id: int = 0

    @property
    def cache_id(self) -> int:
        return self._cache_id

    @cache_id.setter
    def cache_id(self, value: int) -> None:
        self._cache_id = value

    def get_serializer(self) -> Serializer:
        return self._serializer

    def _create_named_cache_request(self, request: any, request_type: NamedCacheRequestType) -> NamedCacheRequest:
        any_cache_request = GrpcAny()
        any_cache_request.Pack(request)

        return NamedCacheRequest(
            type=request_type,
            cacheId=self.cache_id,
            message=any_cache_request,
        )

    @staticmethod
    def create_proxy_request(named_cache_request: NamedCacheRequest) -> ProxyRequest:
        any_named_cache_request = GrpcAny()
        any_named_cache_request.Pack(named_cache_request)
        req_id = RequestIdGenerator.next()
        proxy_request = ProxyRequest(
            id=req_id,
            message=any_named_cache_request,
        )
        return proxy_request

    @staticmethod
    def ensure_request(cache_name: str) -> NamedCacheRequest:
        cache_request = EnsureCacheRequest(cache=cache_name)

        any_cache_request = GrpcAny()
        any_cache_request.Pack(cache_request)

        named_cache_request = NamedCacheRequest(
            type=NamedCacheRequestType.EnsureCache,
            message=any_cache_request,
        )
        return named_cache_request

    def put_request(self, key: K, value: V, ttl: int = 0) -> NamedCacheRequest:
        return self._create_named_cache_request(
            PutRequest(
                key=self._serializer.serialize(key),  # Serialized key
                value=self._serializer.serialize(value),  # Serialized value
                ttl=ttl,
            ),
            NamedCacheRequestType.Put,
        )

    def get_request(self, key: K) -> NamedCacheRequest:
        return self._create_named_cache_request(
            BytesValue(value=self._serializer.serialize(key)), NamedCacheRequestType.Get
        )

    def get_all_request(self, keys: set[K]) -> NamedCacheRequest:
        if keys is None:
            raise ValueError("Must specify a set of keys")

        return self._create_named_cache_request(
            CollectionOfBytesValues(
                values=list(self._serializer.serialize(k) for k in keys),
            ),
            NamedCacheRequestType.GetAll,
        )

    def put_if_absent_request(self, key: K, value: V, ttl: int = 0) -> NamedCacheRequest:

        return self._create_named_cache_request(
            PutRequest(
                key=self._serializer.serialize(key),  # Serialized key
                value=self._serializer.serialize(value),  # Serialized value
                ttl=ttl,
            ),
            NamedCacheRequestType.PutIfAbsent,
        )

    def put_all_request(self, kv_map: dict[K, V], ttl: Optional[int] = 0) -> NamedCacheRequest:
        return self._create_named_cache_request(
            PutAllRequest(
                entries=list(
                    BinaryKeyAndValue(key=self._serializer.serialize(k), value=self._serializer.serialize(v))
                    for k, v in kv_map.items()
                ),
                ttl=ttl,
            ),
            NamedCacheRequestType.PutAll,
        )

    def clear_request(self) -> NamedCacheRequest:
        named_cache_request = NamedCacheRequest(
            type=NamedCacheRequestType.Clear,
            cacheId=self.cache_id,
        )
        return named_cache_request

    def destroy_request(self) -> NamedCacheRequest:
        named_cache_request = NamedCacheRequest(
            type=NamedCacheRequestType.Destroy,
            cacheId=self.cache_id,
        )
        return named_cache_request

    def truncate_request(self) -> NamedCacheRequest:
        named_cache_request = NamedCacheRequest(
            type=NamedCacheRequestType.Truncate,
            cacheId=self.cache_id,
        )
        return named_cache_request

    def remove_request(self, key: K) -> NamedCacheRequest:
        return self._create_named_cache_request(
            BytesValue(value=self._serializer.serialize(key)), NamedCacheRequestType.Remove
        )

    def remove_mapping_request(self, key: K, value: V) -> NamedCacheRequest:
        return self._create_named_cache_request(
            BinaryKeyAndValue(key=self._serializer.serialize(key), value=self._serializer.serialize(value)),
            NamedCacheRequestType.RemoveMapping,
        )

    def replace_request(self, key: K, value: V) -> NamedCacheRequest:
        return self._create_named_cache_request(
            BinaryKeyAndValue(key=self._serializer.serialize(key), value=self._serializer.serialize(value)),
            NamedCacheRequestType.Replace,
        )

    def replace_mapping_request(self, key: K, old_value: V, new_value: V) -> NamedCacheRequest:
        return self._create_named_cache_request(
            ReplaceMappingRequest(
                key=self._serializer.serialize(key),
                previousValue=self._serializer.serialize(old_value),
                newValue=self._serializer.serialize(new_value),
            ),
            NamedCacheRequestType.ReplaceMapping,
        )

    def contains_key_request(self, key: K) -> NamedCacheRequest:
        return self._create_named_cache_request(
            BytesValue(value=self._serializer.serialize(key)), NamedCacheRequestType.ContainsKey
        )

    def contains_value_request(self, value: V) -> NamedCacheRequest:
        return self._create_named_cache_request(
            BytesValue(value=self._serializer.serialize(value)), NamedCacheRequestType.ContainsValue
        )

    def is_empty_request(self) -> NamedCacheRequest:
        named_cache_request = NamedCacheRequest(
            type=NamedCacheRequestType.IsEmpty,
            cacheId=self.cache_id,
        )
        return named_cache_request

    def size_request(self) -> NamedCacheRequest:
        named_cache_request = NamedCacheRequest(
            type=NamedCacheRequestType.Size,
            cacheId=self.cache_id,
        )
        return named_cache_request

    def invoke_request(self, key: K, processor: EntryProcessor[R]) -> NamedCacheRequest:
        return self._create_named_cache_request(
            ExecuteRequest(
                agent=self._serializer.serialize(processor),
                keys=KeysOrFilter(
                    key=self._serializer.serialize(key),
                ),
            ),
            NamedCacheRequestType.Invoke,
        )

    def invoke_all_request(
        self, processor: EntryProcessor[R], keys: Optional[set[K]] = None, query_filter: Optional[Filter] = None
    ) -> NamedCacheRequest:
        if keys is not None and query_filter is not None:
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
        elif query_filter is not None:
            cache_request = ExecuteRequest(
                agent=self._serializer.serialize(processor),
                keys=KeysOrFilter(
                    filter=self._serializer.serialize(query_filter),
                ),
            )
        else:
            cache_request = ExecuteRequest(
                agent=self._serializer.serialize(processor),
            )

        return self._create_named_cache_request(cache_request, NamedCacheRequestType.Invoke)

    def aggregate_request(
        self, aggregator: EntryAggregator[R], keys: Optional[set[K]] = None, query_filter: Optional[Filter] = None
    ) -> NamedCacheRequest:
        if keys is not None and query_filter is not None:
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
        elif query_filter is not None:
            cache_request = ExecuteRequest(
                agent=self._serializer.serialize(aggregator),
                keys=KeysOrFilter(
                    filter=self._serializer.serialize(query_filter),
                ),
            )
        else:
            cache_request = ExecuteRequest(
                agent=self._serializer.serialize(aggregator),
            )

        return self._create_named_cache_request(cache_request, NamedCacheRequestType.Aggregate)

    def values_request(
        self, query_filter: Optional[Filter] = None, comparator: Optional[Comparator] = None
    ) -> NamedCacheRequest:
        if query_filter is None and comparator is not None:
            raise ValueError("Filter cannot be None")

        if query_filter is not None:
            query_request = QueryRequest(filter=self._serializer.serialize(query_filter))
        elif comparator is not None:
            query_request = QueryRequest(comparator=self._serializer.serialize(comparator))
        else:
            query_request = QueryRequest()

        return self._create_named_cache_request(query_request, NamedCacheRequestType.QueryValues)

    def keys_request(self, query_filter: Optional[Filter] = None) -> NamedCacheRequest:

        if query_filter is not None:
            query_request = QueryRequest(filter=self._serializer.serialize(query_filter))
        else:
            query_request = QueryRequest()

        return self._create_named_cache_request(query_request, NamedCacheRequestType.QueryKeys)

    def entries_request(
        self, query_filter: Optional[Filter] = None, comparator: Optional[Comparator] = None
    ) -> NamedCacheRequest:
        if query_filter is None and comparator is not None:
            raise ValueError("Filter cannot be None")

        if query_filter is not None:
            query_request = QueryRequest(filter=self._serializer.serialize(query_filter))
        elif comparator is not None:
            query_request = QueryRequest(comparator=self._serializer.serialize(comparator))
        else:
            query_request = QueryRequest()

        return self._create_named_cache_request(query_request, NamedCacheRequestType.QueryEntries)

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
        self, subscribe: bool, lite: bool = False, *, key: Optional[K] = None, query_filter: Optional[Filter] = None
    ) -> MapListenerRequest:
        """Creates a gRPC generated MapListenerRequest"""

        if key is None and query_filter is None:
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
            filter_local: Filter = query_filter if query_filter is not None else Filters.always()
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
    ) -> NamedCacheRequest:
        return self._create_named_cache_request(
            IndexRequest(
                add=True,
                extractor=self._serializer.serialize(extractor),
                sorted=ordered,
            ),
            NamedCacheRequestType.Index,
        )

    def remove_index_request(self, extractor: ValueExtractor[T, E]) -> NamedCacheRequest:
        return self._create_named_cache_request(
            IndexRequest(
                add=False,
                extractor=self._serializer.serialize(extractor),
            ),
            NamedCacheRequestType.Index,
        )
