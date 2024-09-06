# Copyright (c) 2022, 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

import logging
import sys
import threading
from typing import Optional, TypeVar

from google.protobuf.any_pb2 import Any  # type: ignore
from google.protobuf.wrappers_pb2 import BytesValue  # type: ignore

from . import cache_service_messages_v1_pb2, common_messages_v1_pb2, proxy_service_messages_v1_pb2
from .aggregator import EntryAggregator
from .comparator import Comparator
from .extractor import ValueExtractor
from .filter import Filter, Filters, MapEventFilter
from .messages_pb2 import (
    EntrySetRequest,
    KeySetRequest,
    MapListenerRequest,
    PageRequest,
    PutIfAbsentRequest,
    ValuesRequest,
)
from .processor import EntryProcessor
from .serialization import Serializer

E = TypeVar("E")
K = TypeVar("K")
R = TypeVar("R")
T = TypeVar("T")
V = TypeVar("V")

COH_LOG = logging.getLogger("coherence")


class Request_ID_Generator:
    _generator = None

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counter = 0

    @classmethod
    def generator(cls) -> Request_ID_Generator:
        if Request_ID_Generator._generator is None:
            Request_ID_Generator._generator = Request_ID_Generator()
        return Request_ID_Generator._generator

    @classmethod
    def get_next_id(cls) -> int:
        generator = cls.generator()
        with generator._lock:
            if generator._counter == sys.maxsize:
                generator._counter = 0
            else:
                generator._counter += 1
            return generator._counter


class RequestFactory_v1:

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

    def create_proxy_request(
        self, named_cache_request: cache_service_messages_v1_pb2.NamedCacheRequest
    ) -> proxy_service_messages_v1_pb2.ProxyRequest:
        any_named_cache_request = Any()
        any_named_cache_request.Pack(named_cache_request)
        req_id = Request_ID_Generator.get_next_id()
        proxy_request = proxy_service_messages_v1_pb2.ProxyRequest(
            id=req_id,
            message=any_named_cache_request,
        )
        return proxy_request

    def ensure_request(self, cache_name: str) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        cache_request = cache_service_messages_v1_pb2.EnsureCacheRequest(cache=cache_name)

        any_cache_request = Any()
        any_cache_request.Pack(cache_request)

        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.EnsureCache,
            message=any_cache_request,
        )
        return named_cache_request

    def put_request(self, key: K, value: V, ttl: int = -1) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        cache_request = cache_service_messages_v1_pb2.PutRequest(
            key=self._serializer.serialize(key),  # Serialized key
            value=self._serializer.serialize(value),  # Serialized value
            ttl=ttl,
        )

        any_cache_request = Any()
        any_cache_request.Pack(cache_request)

        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.Put,
            cacheId=self.cache_id,
            message=any_cache_request,
        )

        return named_cache_request

    def get_request(self, key: K) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        cache_request = BytesValue(value=self._serializer.serialize(key))

        any_cache_request = Any()
        any_cache_request.Pack(cache_request)

        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.Get,
            cacheId=self.cache_id,
            message=any_cache_request,
        )

        return named_cache_request

    def get_all_request(self, keys: set[K]) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        if keys is None:
            raise ValueError("Must specify a set of keys")

        lst = list()
        for k in keys:
            lst.append(self._serializer.serialize(k))
        cache_request = common_messages_v1_pb2.CollectionOfBytesValues(
            values=lst,
        )

        any_cache_request = Any()
        any_cache_request.Pack(cache_request)

        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.GetAll,
            cacheId=self.cache_id,
            message=any_cache_request,
        )

        return named_cache_request

    def put_if_absent_request(self, key: K, value: V, ttl: int = -1) -> PutIfAbsentRequest:
        cache_request = cache_service_messages_v1_pb2.PutRequest(
            key=self._serializer.serialize(key),  # Serialized key
            value=self._serializer.serialize(value),  # Serialized value
            ttl=ttl,
        )

        any_cache_request = Any()
        any_cache_request.Pack(cache_request)

        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.PutIfAbsent,
            cacheId=self.cache_id,
            message=any_cache_request,
        )

        return named_cache_request

    def put_all_request(
        self, map: dict[K, V], ttl: Optional[int] = 0
    ) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        entry_list = list()
        for key, value in map.items():
            k = self._serializer.serialize(key)
            v = self._serializer.serialize(value)
            e = common_messages_v1_pb2.BinaryKeyAndValue(key=k, value=v)
            entry_list.append(e)
        cache_request = cache_service_messages_v1_pb2.PutAllRequest(
            entries=entry_list,
            ttl=ttl,
        )

        any_cache_request = Any()
        any_cache_request.Pack(cache_request)

        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.PutAll,
            cacheId=self.cache_id,
            message=any_cache_request,
        )

        return named_cache_request

    def clear_request(self) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.Clear,
            cacheId=self.cache_id,
        )
        return named_cache_request

    def destroy_request(self) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.Destroy,
            cacheId=self.cache_id,
        )
        return named_cache_request

    def truncate_request(self) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.Truncate,
            cacheId=self.cache_id,
        )
        return named_cache_request

    def remove_request(self, key: K) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        cache_request = BytesValue(value=self._serializer.serialize(key))

        any_cache_request = Any()
        any_cache_request.Pack(cache_request)

        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.Remove,
            cacheId=self.cache_id,
            message=any_cache_request,
        )

        return named_cache_request

    def remove_mapping_request(self, key: K, value: V) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        cache_request = common_messages_v1_pb2.BinaryKeyAndValue(
            key=self._serializer.serialize(key), value=self._serializer.serialize(value)
        )

        any_cache_request = Any()
        any_cache_request.Pack(cache_request)

        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.RemoveMapping,
            cacheId=self.cache_id,
            message=any_cache_request,
        )

        return named_cache_request

    def replace_request(self, key: K, value: V) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        cache_request = common_messages_v1_pb2.BinaryKeyAndValue(
            key=self._serializer.serialize(key), value=self._serializer.serialize(value)
        )

        any_cache_request = Any()
        any_cache_request.Pack(cache_request)

        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.Replace,
            cacheId=self.cache_id,
            message=any_cache_request,
        )

        return named_cache_request

    def replace_mapping_request(
        self, key: K, old_value: V, new_value: V
    ) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        cache_request = cache_service_messages_v1_pb2.ReplaceMappingRequest(
            key=self._serializer.serialize(key),
            previousValue=self._serializer.serialize(old_value),
            newValue=self._serializer.serialize(new_value),
        )

        any_cache_request = Any()
        any_cache_request.Pack(cache_request)

        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.ReplaceMapping,
            cacheId=self.cache_id,
            message=any_cache_request,
        )

        return named_cache_request

    def contains_key_request(self, key: K) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        cache_request = BytesValue(value=self._serializer.serialize(key))

        any_cache_request = Any()
        any_cache_request.Pack(cache_request)

        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.ContainsKey,
            cacheId=self.cache_id,
            message=any_cache_request,
        )

        return named_cache_request

    def contains_value_request(self, value: V) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        cache_request = BytesValue(value=self._serializer.serialize(value))

        any_cache_request = Any()
        any_cache_request.Pack(cache_request)

        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.ContainsValue,
            cacheId=self.cache_id,
            message=any_cache_request,
        )

        return named_cache_request

    def is_empty_request(self) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.IsEmpty,
            cacheId=self.cache_id,
        )
        return named_cache_request

    def size_request(self) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.Size,
            cacheId=self.cache_id,
        )
        return named_cache_request

    def invoke_request(self, key: K, processor: EntryProcessor[R]) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        cache_request = cache_service_messages_v1_pb2.ExecuteRequest(
            agent=self._serializer.serialize(processor),
            keys=cache_service_messages_v1_pb2.KeysOrFilter(
                key=self._serializer.serialize(key),
            ),
        )

        any_cache_request = Any()
        any_cache_request.Pack(cache_request)

        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.Invoke,
            cacheId=self.cache_id,
            message=any_cache_request,
        )

        return named_cache_request

    def invoke_all_request(
        self, processor: EntryProcessor[R], keys: Optional[set[K]] = None, filter: Optional[Filter] = None
    ) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        if keys is not None and filter is not None:
            raise ValueError("keys and filter are mutually exclusive")

        if keys is not None:
            list_of_keys = list()
            for key in keys:
                list_of_keys.append(self._serializer.serialize(key))
            cache_request = cache_service_messages_v1_pb2.ExecuteRequest(
                agent=self._serializer.serialize(processor),
                keys=cache_service_messages_v1_pb2.KeysOrFilter(
                    keys=common_messages_v1_pb2.CollectionOfBytesValues(
                        values=list_of_keys,
                    ),
                ),
            )
        elif filter is not None:
            cache_request = cache_service_messages_v1_pb2.ExecuteRequest(
                agent=self._serializer.serialize(processor),
                keys=cache_service_messages_v1_pb2.KeysOrFilter(
                    filter=self._serializer.serialize(filter),
                ),
            )
        else:
            cache_request = cache_service_messages_v1_pb2.ExecuteRequest(
                agent=self._serializer.serialize(processor),
            )

        any_cache_request = Any()
        any_cache_request.Pack(cache_request)

        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.Invoke,
            cacheId=self.cache_id,
            message=any_cache_request,
        )

        return named_cache_request

    def aggregate_request(
        self, aggregator: EntryAggregator[R], keys: Optional[set[K]] = None, filter: Optional[Filter] = None
    ) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        if keys is not None and filter is not None:
            raise ValueError("keys and filter are mutually exclusive")

        if keys is not None:
            list_of_keys = list()
            for key in keys:
                list_of_keys.append(self._serializer.serialize(key))
            cache_request = cache_service_messages_v1_pb2.ExecuteRequest(
                agent=self._serializer.serialize(aggregator),
                keys=cache_service_messages_v1_pb2.KeysOrFilter(
                    keys=common_messages_v1_pb2.CollectionOfBytesValues(
                        values=list_of_keys,
                    ),
                ),
            )
        elif filter is not None:
            cache_request = cache_service_messages_v1_pb2.ExecuteRequest(
                agent=self._serializer.serialize(aggregator),
                keys=cache_service_messages_v1_pb2.KeysOrFilter(
                    filter=self._serializer.serialize(filter),
                ),
            )
        else:
            cache_request = cache_service_messages_v1_pb2.ExecuteRequest(
                agent=self._serializer.serialize(aggregator),
            )

        any_cache_request = Any()
        any_cache_request.Pack(cache_request)

        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.Aggregate,
            cacheId=self.cache_id,
            message=any_cache_request,
        )

        return named_cache_request

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
    ) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        cache_request = cache_service_messages_v1_pb2.IndexRequest(
            add=True,
            extractor=self._serializer.serialize(extractor),
            sorted=ordered,
        )
        if comparator is not None:
            cache_request.comparator = self._serializer.serialize(comparator)

        any_cache_request = Any()
        any_cache_request.Pack(cache_request)

        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.Index,
            cacheId=self.cache_id,
            message=any_cache_request,
        )

        return named_cache_request

    def remove_index_request(self, extractor: ValueExtractor[T, E]) -> cache_service_messages_v1_pb2.NamedCacheRequest:
        cache_request = cache_service_messages_v1_pb2.IndexRequest(
            add=False,
            extractor=self._serializer.serialize(extractor),
        )

        any_cache_request = Any()
        any_cache_request.Pack(cache_request)

        named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
            type=cache_service_messages_v1_pb2.NamedCacheRequestType.Index,
            cacheId=self.cache_id,
            message=any_cache_request,
        )

        return named_cache_request
