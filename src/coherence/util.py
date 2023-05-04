# Copyright (c) 2022, 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

import time
from typing import Optional, TypeVar

from .aggregator import EntryAggregator
from .comparator import Comparator
from .filter import Filter, Filters, MapEventFilter
from .messages_pb2 import (  # type: ignore
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

E = TypeVar("E")
K = TypeVar("K")
R = TypeVar("R")
T = TypeVar("T")
V = TypeVar("V")


class RequestFactory:
    def __init__(self, cache_name: str, scope: str, serializer: Serializer) -> None:
        self._cache_name: str = cache_name
        self._scope: str = scope
        self._serializer: Serializer = serializer
        self.__uidPrefix: str = "-" + cache_name + "-" + str(time.time_ns())
        self.__next_request_id: int = 0
        self.__next_filter_id: int = 0

    def get_serializer(self) -> Serializer:
        return self._serializer

    def put_request(self, key: K, value: V, ttl: int = -1) -> PutRequest:
        p = PutRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format(),
            key=self._serializer.serialize(key),
            value=self._serializer.serialize(value),
            ttl=ttl,
        )
        return p

    def get_request(self, key: K) -> GetRequest:
        g = GetRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format(),
            key=self._serializer.serialize(key),
        )
        return g

    def get_all_request(self, keys: set[K]) -> GetRequest:
        if keys is None:
            raise ValueError("Must specify a set of keys")

        g: GetAllRequest = GetAllRequest(scope=self._scope, cache=self._cache_name, format=self._serializer.format())

        for key in keys:
            g.key.append(self._serializer.serialize(key))

        return g

    def put_if_absent_request(self, key: K, value: V, ttl: int = -1) -> PutIfAbsentRequest:
        p = PutIfAbsentRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format(),
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
        p = PutAllRequest(scope=self._scope, cache=self._cache_name, format=self._serializer.format(), entry=entry_list)
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
            format=self._serializer.format(),
            key=self._serializer.serialize(key),
        )
        return r

    def remove_mapping_request(self, key: K, value: V) -> RemoveMappingRequest:
        r = RemoveMappingRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format(),
            key=self._serializer.serialize(key),
            value=self._serializer.serialize(value),
        )
        return r

    def replace_request(self, key: K, value: V) -> ReplaceRequest:
        r = ReplaceRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format(),
            key=self._serializer.serialize(key),
            value=self._serializer.serialize(value),
        )
        return r

    def replace_mapping_request(self, key: K, old_value: V, new_value: V) -> ReplaceMappingRequest:
        r = ReplaceMappingRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format(),
            key=self._serializer.serialize(key),
            previousValue=self._serializer.serialize(old_value),
            newValue=self._serializer.serialize(new_value),
        )
        return r

    def contains_key_request(self, key: K) -> ContainsKeyRequest:
        r = ContainsKeyRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format(),
            key=self._serializer.serialize(key),
        )
        return r

    def contains_value_request(self, value: V) -> ContainsValueRequest:
        r = ContainsValueRequest(
            scope=self._scope,
            cache=self._cache_name,
            format=self._serializer.format(),
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
            format=self._serializer.format(),
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
            format=self._serializer.format(),
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
            format=self._serializer.format(),
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
            format=self._serializer.format(),
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
            format=self._serializer.format(),
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
            format=self._serializer.format(),
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
            scope=self._scope, cache=self._cache_name, format=self._serializer.format(), cookie=cookie
        )

        return r

    def map_listener_request(
        self, subscribe: bool, lite: bool = False, *, key: Optional[K] = None, filter: Optional[Filter] = None
    ) -> MapListenerRequest:
        """Creates a gRPC generated MapListenerRequest"""

        if key is None and filter is None:
            raise AssertionError("Must specify a key or a filter")

        request: MapListenerRequest = MapListenerRequest(
            cache=self._cache_name, scope=self._scope, format=self._serializer.format()
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
            cache=self._cache_name, scope=self._scope, format=self._serializer.format()
        )
        request.uid = self.__generate_next_request_id("init")
        request.subscribe = True
        request.type = MapListenerRequest.RequestType.INIT

        return request

    def __generate_next_request_id(self, prefix: str) -> str:
        """Generates a prefix map-specific prefix when starting a MapEvent gRPC stream."""
        self.__next_request_id += 1
        return prefix + self.__uidPrefix + str(self.__next_request_id)
