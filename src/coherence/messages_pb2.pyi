# mypy: ignore-errors
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AddIndexRequest(_message.Message):
    __slots__ = ["cache", "comparator", "extractor", "format", "scope", "sorted"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    COMPARATOR_FIELD_NUMBER: _ClassVar[int]
    EXTRACTOR_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    SORTED_FIELD_NUMBER: _ClassVar[int]
    cache: str
    comparator: bytes
    extractor: bytes
    format: str
    scope: str
    sorted: bool
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., extractor: _Optional[bytes] = ..., sorted: bool = ..., comparator: _Optional[bytes] = ...) -> None: ...

class AggregateRequest(_message.Message):
    __slots__ = ["aggregator", "cache", "filter", "format", "keys", "scope"]
    AGGREGATOR_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    KEYS_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    aggregator: bytes
    cache: str
    filter: bytes
    format: str
    keys: _containers.RepeatedScalarFieldContainer[bytes]
    scope: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., aggregator: _Optional[bytes] = ..., keys: _Optional[_Iterable[bytes]] = ..., filter: _Optional[bytes] = ...) -> None: ...

class CacheDestroyedResponse(_message.Message):
    __slots__ = ["cache"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    def __init__(self, cache: _Optional[str] = ...) -> None: ...

class CacheTruncatedResponse(_message.Message):
    __slots__ = ["cache"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    def __init__(self, cache: _Optional[str] = ...) -> None: ...

class ClearRequest(_message.Message):
    __slots__ = ["cache", "scope"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    scope: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ...) -> None: ...

class ContainsEntryRequest(_message.Message):
    __slots__ = ["cache", "format", "key", "scope", "value"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    format: str
    key: bytes
    scope: str
    value: bytes
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., key: _Optional[bytes] = ..., value: _Optional[bytes] = ...) -> None: ...

class ContainsKeyRequest(_message.Message):
    __slots__ = ["cache", "format", "key", "scope"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    format: str
    key: bytes
    scope: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., key: _Optional[bytes] = ...) -> None: ...

class ContainsValueRequest(_message.Message):
    __slots__ = ["cache", "format", "scope", "value"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    format: str
    scope: str
    value: bytes
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., value: _Optional[bytes] = ...) -> None: ...

class DestroyRequest(_message.Message):
    __slots__ = ["cache", "scope"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    scope: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ...) -> None: ...

class Entry(_message.Message):
    __slots__ = ["key", "value"]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: bytes
    value: bytes
    def __init__(self, key: _Optional[bytes] = ..., value: _Optional[bytes] = ...) -> None: ...

class EntryResult(_message.Message):
    __slots__ = ["cookie", "key", "value"]
    COOKIE_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    cookie: bytes
    key: bytes
    value: bytes
    def __init__(self, key: _Optional[bytes] = ..., value: _Optional[bytes] = ..., cookie: _Optional[bytes] = ...) -> None: ...

class EntrySetRequest(_message.Message):
    __slots__ = ["cache", "comparator", "filter", "format", "scope"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    COMPARATOR_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    comparator: bytes
    filter: bytes
    format: str
    scope: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., filter: _Optional[bytes] = ..., comparator: _Optional[bytes] = ...) -> None: ...

class GetAllRequest(_message.Message):
    __slots__ = ["cache", "format", "key", "scope"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    format: str
    key: _containers.RepeatedScalarFieldContainer[bytes]
    scope: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., key: _Optional[_Iterable[bytes]] = ...) -> None: ...

class GetRequest(_message.Message):
    __slots__ = ["cache", "format", "key", "scope"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    format: str
    key: bytes
    scope: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., key: _Optional[bytes] = ...) -> None: ...

class InvokeAllRequest(_message.Message):
    __slots__ = ["cache", "filter", "format", "keys", "processor", "scope"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    KEYS_FIELD_NUMBER: _ClassVar[int]
    PROCESSOR_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    filter: bytes
    format: str
    keys: _containers.RepeatedScalarFieldContainer[bytes]
    processor: bytes
    scope: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., processor: _Optional[bytes] = ..., keys: _Optional[_Iterable[bytes]] = ..., filter: _Optional[bytes] = ...) -> None: ...

class InvokeRequest(_message.Message):
    __slots__ = ["cache", "format", "key", "processor", "scope"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    PROCESSOR_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    format: str
    key: bytes
    processor: bytes
    scope: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., processor: _Optional[bytes] = ..., key: _Optional[bytes] = ...) -> None: ...

class IsEmptyRequest(_message.Message):
    __slots__ = ["cache", "scope"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    scope: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ...) -> None: ...

class IsReadyRequest(_message.Message):
    __slots__ = ["cache", "scope"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    scope: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ...) -> None: ...

class KeySetRequest(_message.Message):
    __slots__ = ["cache", "filter", "format", "scope"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    filter: bytes
    format: str
    scope: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., filter: _Optional[bytes] = ...) -> None: ...

class MapEventResponse(_message.Message):
    __slots__ = ["filterIds", "id", "key", "newValue", "oldValue", "priming", "synthetic", "transformationState"]
    class TransformationState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    FILTERIDS_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    NEWVALUE_FIELD_NUMBER: _ClassVar[int]
    NON_TRANSFORMABLE: MapEventResponse.TransformationState
    OLDVALUE_FIELD_NUMBER: _ClassVar[int]
    PRIMING_FIELD_NUMBER: _ClassVar[int]
    SYNTHETIC_FIELD_NUMBER: _ClassVar[int]
    TRANSFORMABLE: MapEventResponse.TransformationState
    TRANSFORMATIONSTATE_FIELD_NUMBER: _ClassVar[int]
    TRANSFORMED: MapEventResponse.TransformationState
    filterIds: _containers.RepeatedScalarFieldContainer[int]
    id: int
    key: bytes
    newValue: bytes
    oldValue: bytes
    priming: bool
    synthetic: bool
    transformationState: MapEventResponse.TransformationState
    def __init__(self, id: _Optional[int] = ..., key: _Optional[bytes] = ..., newValue: _Optional[bytes] = ..., oldValue: _Optional[bytes] = ..., transformationState: _Optional[_Union[MapEventResponse.TransformationState, str]] = ..., filterIds: _Optional[_Iterable[int]] = ..., synthetic: bool = ..., priming: bool = ...) -> None: ...

class MapListenerErrorResponse(_message.Message):
    __slots__ = ["code", "message", "stack", "uid"]
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    STACK_FIELD_NUMBER: _ClassVar[int]
    UID_FIELD_NUMBER: _ClassVar[int]
    code: int
    message: str
    stack: _containers.RepeatedScalarFieldContainer[str]
    uid: str
    def __init__(self, uid: _Optional[str] = ..., message: _Optional[str] = ..., code: _Optional[int] = ..., stack: _Optional[_Iterable[str]] = ...) -> None: ...

class MapListenerRequest(_message.Message):
    __slots__ = ["cache", "filter", "filterId", "format", "key", "lite", "priming", "scope", "subscribe", "trigger", "type", "uid"]
    class RequestType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FILTER: MapListenerRequest.RequestType
    FILTERID_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    INIT: MapListenerRequest.RequestType
    KEY: MapListenerRequest.RequestType
    KEY_FIELD_NUMBER: _ClassVar[int]
    LITE_FIELD_NUMBER: _ClassVar[int]
    PRIMING_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    SUBSCRIBE_FIELD_NUMBER: _ClassVar[int]
    TRIGGER_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    UID_FIELD_NUMBER: _ClassVar[int]
    cache: str
    filter: bytes
    filterId: int
    format: str
    key: bytes
    lite: bool
    priming: bool
    scope: str
    subscribe: bool
    trigger: bytes
    type: MapListenerRequest.RequestType
    uid: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., uid: _Optional[str] = ..., type: _Optional[_Union[MapListenerRequest.RequestType, str]] = ..., filter: _Optional[bytes] = ..., key: _Optional[bytes] = ..., lite: bool = ..., subscribe: bool = ..., priming: bool = ..., trigger: _Optional[bytes] = ..., filterId: _Optional[int] = ...) -> None: ...

class MapListenerResponse(_message.Message):
    __slots__ = ["destroyed", "error", "event", "subscribed", "truncated", "unsubscribed"]
    DESTROYED_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    EVENT_FIELD_NUMBER: _ClassVar[int]
    SUBSCRIBED_FIELD_NUMBER: _ClassVar[int]
    TRUNCATED_FIELD_NUMBER: _ClassVar[int]
    UNSUBSCRIBED_FIELD_NUMBER: _ClassVar[int]
    destroyed: CacheDestroyedResponse
    error: MapListenerErrorResponse
    event: MapEventResponse
    subscribed: MapListenerSubscribedResponse
    truncated: CacheTruncatedResponse
    unsubscribed: MapListenerUnsubscribedResponse
    def __init__(self, subscribed: _Optional[_Union[MapListenerSubscribedResponse, _Mapping]] = ..., unsubscribed: _Optional[_Union[MapListenerUnsubscribedResponse, _Mapping]] = ..., event: _Optional[_Union[MapEventResponse, _Mapping]] = ..., error: _Optional[_Union[MapListenerErrorResponse, _Mapping]] = ..., destroyed: _Optional[_Union[CacheDestroyedResponse, _Mapping]] = ..., truncated: _Optional[_Union[CacheTruncatedResponse, _Mapping]] = ...) -> None: ...

class MapListenerSubscribedResponse(_message.Message):
    __slots__ = ["uid"]
    UID_FIELD_NUMBER: _ClassVar[int]
    uid: str
    def __init__(self, uid: _Optional[str] = ...) -> None: ...

class MapListenerUnsubscribedResponse(_message.Message):
    __slots__ = ["uid"]
    UID_FIELD_NUMBER: _ClassVar[int]
    uid: str
    def __init__(self, uid: _Optional[str] = ...) -> None: ...

class OptionalValue(_message.Message):
    __slots__ = ["present", "value"]
    PRESENT_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    present: bool
    value: bytes
    def __init__(self, present: bool = ..., value: _Optional[bytes] = ...) -> None: ...

class PageRequest(_message.Message):
    __slots__ = ["cache", "cookie", "format", "scope"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    COOKIE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    cookie: bytes
    format: str
    scope: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., cookie: _Optional[bytes] = ...) -> None: ...

class PutAllRequest(_message.Message):
    __slots__ = ["cache", "entry", "format", "scope", "ttl"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    ENTRY_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    TTL_FIELD_NUMBER: _ClassVar[int]
    cache: str
    entry: _containers.RepeatedCompositeFieldContainer[Entry]
    format: str
    scope: str
    ttl: int
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., entry: _Optional[_Iterable[_Union[Entry, _Mapping]]] = ..., ttl: _Optional[int] = ...) -> None: ...

class PutIfAbsentRequest(_message.Message):
    __slots__ = ["cache", "format", "key", "scope", "ttl", "value"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    TTL_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    format: str
    key: bytes
    scope: str
    ttl: int
    value: bytes
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., key: _Optional[bytes] = ..., value: _Optional[bytes] = ..., ttl: _Optional[int] = ...) -> None: ...

class PutRequest(_message.Message):
    __slots__ = ["cache", "format", "key", "scope", "ttl", "value"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    TTL_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    format: str
    key: bytes
    scope: str
    ttl: int
    value: bytes
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., key: _Optional[bytes] = ..., value: _Optional[bytes] = ..., ttl: _Optional[int] = ...) -> None: ...

class RemoveIndexRequest(_message.Message):
    __slots__ = ["cache", "extractor", "format", "scope"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    EXTRACTOR_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    extractor: bytes
    format: str
    scope: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., extractor: _Optional[bytes] = ...) -> None: ...

class RemoveMappingRequest(_message.Message):
    __slots__ = ["cache", "format", "key", "scope", "value"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    format: str
    key: bytes
    scope: str
    value: bytes
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., key: _Optional[bytes] = ..., value: _Optional[bytes] = ...) -> None: ...

class RemoveRequest(_message.Message):
    __slots__ = ["cache", "format", "key", "scope"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    format: str
    key: bytes
    scope: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., key: _Optional[bytes] = ...) -> None: ...

class ReplaceMappingRequest(_message.Message):
    __slots__ = ["cache", "format", "key", "newValue", "previousValue", "scope"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    NEWVALUE_FIELD_NUMBER: _ClassVar[int]
    PREVIOUSVALUE_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    format: str
    key: bytes
    newValue: bytes
    previousValue: bytes
    scope: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., key: _Optional[bytes] = ..., previousValue: _Optional[bytes] = ..., newValue: _Optional[bytes] = ...) -> None: ...

class ReplaceRequest(_message.Message):
    __slots__ = ["cache", "format", "key", "scope", "value"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    format: str
    key: bytes
    scope: str
    value: bytes
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., key: _Optional[bytes] = ..., value: _Optional[bytes] = ...) -> None: ...

class SizeRequest(_message.Message):
    __slots__ = ["cache", "scope"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    scope: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ...) -> None: ...

class TruncateRequest(_message.Message):
    __slots__ = ["cache", "scope"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    scope: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ...) -> None: ...

class ValuesRequest(_message.Message):
    __slots__ = ["cache", "comparator", "filter", "format", "scope"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    COMPARATOR_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    comparator: bytes
    filter: bytes
    format: str
    scope: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., filter: _Optional[bytes] = ..., comparator: _Optional[bytes] = ...) -> None: ...
