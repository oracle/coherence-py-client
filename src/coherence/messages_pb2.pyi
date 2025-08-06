from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ClearRequest(_message.Message):
    __slots__ = ("scope", "cache")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ...) -> None: ...

class ContainsEntryRequest(_message.Message):
    __slots__ = ("scope", "cache", "format", "key", "value")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    format: str
    key: bytes
    value: bytes
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., key: _Optional[bytes] = ..., value: _Optional[bytes] = ...) -> None: ...

class ContainsKeyRequest(_message.Message):
    __slots__ = ("scope", "cache", "format", "key")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    format: str
    key: bytes
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., key: _Optional[bytes] = ...) -> None: ...

class ContainsValueRequest(_message.Message):
    __slots__ = ("scope", "cache", "format", "value")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    format: str
    value: bytes
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., value: _Optional[bytes] = ...) -> None: ...

class DestroyRequest(_message.Message):
    __slots__ = ("scope", "cache")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ...) -> None: ...

class IsEmptyRequest(_message.Message):
    __slots__ = ("scope", "cache")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ...) -> None: ...

class IsReadyRequest(_message.Message):
    __slots__ = ("scope", "cache")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ...) -> None: ...

class SizeRequest(_message.Message):
    __slots__ = ("scope", "cache")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ...) -> None: ...

class GetRequest(_message.Message):
    __slots__ = ("scope", "cache", "format", "key")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    format: str
    key: bytes
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., key: _Optional[bytes] = ...) -> None: ...

class GetAllRequest(_message.Message):
    __slots__ = ("scope", "cache", "format", "key")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    format: str
    key: _containers.RepeatedScalarFieldContainer[bytes]
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., key: _Optional[_Iterable[bytes]] = ...) -> None: ...

class PutRequest(_message.Message):
    __slots__ = ("scope", "cache", "format", "key", "value", "ttl")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    TTL_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    format: str
    key: bytes
    value: bytes
    ttl: int
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., key: _Optional[bytes] = ..., value: _Optional[bytes] = ..., ttl: _Optional[int] = ...) -> None: ...

class PutAllRequest(_message.Message):
    __slots__ = ("scope", "cache", "format", "entry", "ttl")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    ENTRY_FIELD_NUMBER: _ClassVar[int]
    TTL_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    format: str
    entry: _containers.RepeatedCompositeFieldContainer[Entry]
    ttl: int
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., entry: _Optional[_Iterable[_Union[Entry, _Mapping]]] = ..., ttl: _Optional[int] = ...) -> None: ...

class PutIfAbsentRequest(_message.Message):
    __slots__ = ("scope", "cache", "format", "key", "value", "ttl")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    TTL_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    format: str
    key: bytes
    value: bytes
    ttl: int
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., key: _Optional[bytes] = ..., value: _Optional[bytes] = ..., ttl: _Optional[int] = ...) -> None: ...

class RemoveRequest(_message.Message):
    __slots__ = ("scope", "cache", "format", "key")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    format: str
    key: bytes
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., key: _Optional[bytes] = ...) -> None: ...

class RemoveMappingRequest(_message.Message):
    __slots__ = ("scope", "cache", "format", "key", "value")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    format: str
    key: bytes
    value: bytes
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., key: _Optional[bytes] = ..., value: _Optional[bytes] = ...) -> None: ...

class ReplaceRequest(_message.Message):
    __slots__ = ("scope", "cache", "format", "key", "value")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    format: str
    key: bytes
    value: bytes
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., key: _Optional[bytes] = ..., value: _Optional[bytes] = ...) -> None: ...

class ReplaceMappingRequest(_message.Message):
    __slots__ = ("scope", "cache", "format", "key", "previousValue", "newValue")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    PREVIOUSVALUE_FIELD_NUMBER: _ClassVar[int]
    NEWVALUE_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    format: str
    key: bytes
    previousValue: bytes
    newValue: bytes
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., key: _Optional[bytes] = ..., previousValue: _Optional[bytes] = ..., newValue: _Optional[bytes] = ...) -> None: ...

class PageRequest(_message.Message):
    __slots__ = ("scope", "cache", "format", "cookie")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    COOKIE_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    format: str
    cookie: bytes
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., cookie: _Optional[bytes] = ...) -> None: ...

class EntryResult(_message.Message):
    __slots__ = ("key", "value", "cookie")
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    COOKIE_FIELD_NUMBER: _ClassVar[int]
    key: bytes
    value: bytes
    cookie: bytes
    def __init__(self, key: _Optional[bytes] = ..., value: _Optional[bytes] = ..., cookie: _Optional[bytes] = ...) -> None: ...

class Entry(_message.Message):
    __slots__ = ("key", "value")
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: bytes
    value: bytes
    def __init__(self, key: _Optional[bytes] = ..., value: _Optional[bytes] = ...) -> None: ...

class TruncateRequest(_message.Message):
    __slots__ = ("scope", "cache")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ...) -> None: ...

class AddIndexRequest(_message.Message):
    __slots__ = ("scope", "cache", "format", "extractor", "sorted", "comparator")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    EXTRACTOR_FIELD_NUMBER: _ClassVar[int]
    SORTED_FIELD_NUMBER: _ClassVar[int]
    COMPARATOR_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    format: str
    extractor: bytes
    sorted: bool
    comparator: bytes
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., extractor: _Optional[bytes] = ..., sorted: bool = ..., comparator: _Optional[bytes] = ...) -> None: ...

class RemoveIndexRequest(_message.Message):
    __slots__ = ("scope", "cache", "format", "extractor")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    EXTRACTOR_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    format: str
    extractor: bytes
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., extractor: _Optional[bytes] = ...) -> None: ...

class AggregateRequest(_message.Message):
    __slots__ = ("scope", "cache", "format", "aggregator", "keys", "filter")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    AGGREGATOR_FIELD_NUMBER: _ClassVar[int]
    KEYS_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    format: str
    aggregator: bytes
    keys: _containers.RepeatedScalarFieldContainer[bytes]
    filter: bytes
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., aggregator: _Optional[bytes] = ..., keys: _Optional[_Iterable[bytes]] = ..., filter: _Optional[bytes] = ...) -> None: ...

class InvokeRequest(_message.Message):
    __slots__ = ("scope", "cache", "format", "processor", "key")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    PROCESSOR_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    format: str
    processor: bytes
    key: bytes
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., processor: _Optional[bytes] = ..., key: _Optional[bytes] = ...) -> None: ...

class InvokeAllRequest(_message.Message):
    __slots__ = ("scope", "cache", "format", "processor", "keys", "filter")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    PROCESSOR_FIELD_NUMBER: _ClassVar[int]
    KEYS_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    format: str
    processor: bytes
    keys: _containers.RepeatedScalarFieldContainer[bytes]
    filter: bytes
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., processor: _Optional[bytes] = ..., keys: _Optional[_Iterable[bytes]] = ..., filter: _Optional[bytes] = ...) -> None: ...

class EntrySetRequest(_message.Message):
    __slots__ = ("scope", "cache", "format", "filter", "comparator")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    COMPARATOR_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    format: str
    filter: bytes
    comparator: bytes
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., filter: _Optional[bytes] = ..., comparator: _Optional[bytes] = ...) -> None: ...

class KeySetRequest(_message.Message):
    __slots__ = ("scope", "cache", "format", "filter")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    format: str
    filter: bytes
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., filter: _Optional[bytes] = ...) -> None: ...

class ValuesRequest(_message.Message):
    __slots__ = ("scope", "cache", "format", "filter", "comparator")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    COMPARATOR_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    format: str
    filter: bytes
    comparator: bytes
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., filter: _Optional[bytes] = ..., comparator: _Optional[bytes] = ...) -> None: ...

class OptionalValue(_message.Message):
    __slots__ = ("present", "value")
    PRESENT_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    present: bool
    value: bytes
    def __init__(self, present: bool = ..., value: _Optional[bytes] = ...) -> None: ...

class MapListenerRequest(_message.Message):
    __slots__ = ("scope", "cache", "format", "uid", "type", "filter", "key", "lite", "subscribe", "priming", "trigger", "filterId", "heartbeatMillis")
    class RequestType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        INIT: _ClassVar[MapListenerRequest.RequestType]
        KEY: _ClassVar[MapListenerRequest.RequestType]
        FILTER: _ClassVar[MapListenerRequest.RequestType]
    INIT: MapListenerRequest.RequestType
    KEY: MapListenerRequest.RequestType
    FILTER: MapListenerRequest.RequestType
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    UID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    LITE_FIELD_NUMBER: _ClassVar[int]
    SUBSCRIBE_FIELD_NUMBER: _ClassVar[int]
    PRIMING_FIELD_NUMBER: _ClassVar[int]
    TRIGGER_FIELD_NUMBER: _ClassVar[int]
    FILTERID_FIELD_NUMBER: _ClassVar[int]
    HEARTBEATMILLIS_FIELD_NUMBER: _ClassVar[int]
    scope: str
    cache: str
    format: str
    uid: str
    type: MapListenerRequest.RequestType
    filter: bytes
    key: bytes
    lite: bool
    subscribe: bool
    priming: bool
    trigger: bytes
    filterId: int
    heartbeatMillis: int
    def __init__(self, scope: _Optional[str] = ..., cache: _Optional[str] = ..., format: _Optional[str] = ..., uid: _Optional[str] = ..., type: _Optional[_Union[MapListenerRequest.RequestType, str]] = ..., filter: _Optional[bytes] = ..., key: _Optional[bytes] = ..., lite: bool = ..., subscribe: bool = ..., priming: bool = ..., trigger: _Optional[bytes] = ..., filterId: _Optional[int] = ..., heartbeatMillis: _Optional[int] = ...) -> None: ...

class MapListenerResponse(_message.Message):
    __slots__ = ("subscribed", "unsubscribed", "event", "error", "destroyed", "truncated", "heartbeat")
    SUBSCRIBED_FIELD_NUMBER: _ClassVar[int]
    UNSUBSCRIBED_FIELD_NUMBER: _ClassVar[int]
    EVENT_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    DESTROYED_FIELD_NUMBER: _ClassVar[int]
    TRUNCATED_FIELD_NUMBER: _ClassVar[int]
    HEARTBEAT_FIELD_NUMBER: _ClassVar[int]
    subscribed: MapListenerSubscribedResponse
    unsubscribed: MapListenerUnsubscribedResponse
    event: MapEventResponse
    error: MapListenerErrorResponse
    destroyed: CacheDestroyedResponse
    truncated: CacheTruncatedResponse
    heartbeat: HeartbeatMessage
    def __init__(self, subscribed: _Optional[_Union[MapListenerSubscribedResponse, _Mapping]] = ..., unsubscribed: _Optional[_Union[MapListenerUnsubscribedResponse, _Mapping]] = ..., event: _Optional[_Union[MapEventResponse, _Mapping]] = ..., error: _Optional[_Union[MapListenerErrorResponse, _Mapping]] = ..., destroyed: _Optional[_Union[CacheDestroyedResponse, _Mapping]] = ..., truncated: _Optional[_Union[CacheTruncatedResponse, _Mapping]] = ..., heartbeat: _Optional[_Union[HeartbeatMessage, _Mapping]] = ...) -> None: ...

class MapListenerSubscribedResponse(_message.Message):
    __slots__ = ("uid",)
    UID_FIELD_NUMBER: _ClassVar[int]
    uid: str
    def __init__(self, uid: _Optional[str] = ...) -> None: ...

class MapListenerUnsubscribedResponse(_message.Message):
    __slots__ = ("uid",)
    UID_FIELD_NUMBER: _ClassVar[int]
    uid: str
    def __init__(self, uid: _Optional[str] = ...) -> None: ...

class CacheDestroyedResponse(_message.Message):
    __slots__ = ("cache",)
    CACHE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    def __init__(self, cache: _Optional[str] = ...) -> None: ...

class CacheTruncatedResponse(_message.Message):
    __slots__ = ("cache",)
    CACHE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    def __init__(self, cache: _Optional[str] = ...) -> None: ...

class MapListenerErrorResponse(_message.Message):
    __slots__ = ("uid", "message", "code", "stack")
    UID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    CODE_FIELD_NUMBER: _ClassVar[int]
    STACK_FIELD_NUMBER: _ClassVar[int]
    uid: str
    message: str
    code: int
    stack: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, uid: _Optional[str] = ..., message: _Optional[str] = ..., code: _Optional[int] = ..., stack: _Optional[_Iterable[str]] = ...) -> None: ...

class MapEventResponse(_message.Message):
    __slots__ = ("id", "key", "newValue", "oldValue", "transformationState", "filterIds", "synthetic", "priming")
    class TransformationState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        NON_TRANSFORMABLE: _ClassVar[MapEventResponse.TransformationState]
        TRANSFORMABLE: _ClassVar[MapEventResponse.TransformationState]
        TRANSFORMED: _ClassVar[MapEventResponse.TransformationState]
    NON_TRANSFORMABLE: MapEventResponse.TransformationState
    TRANSFORMABLE: MapEventResponse.TransformationState
    TRANSFORMED: MapEventResponse.TransformationState
    ID_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    NEWVALUE_FIELD_NUMBER: _ClassVar[int]
    OLDVALUE_FIELD_NUMBER: _ClassVar[int]
    TRANSFORMATIONSTATE_FIELD_NUMBER: _ClassVar[int]
    FILTERIDS_FIELD_NUMBER: _ClassVar[int]
    SYNTHETIC_FIELD_NUMBER: _ClassVar[int]
    PRIMING_FIELD_NUMBER: _ClassVar[int]
    id: int
    key: bytes
    newValue: bytes
    oldValue: bytes
    transformationState: MapEventResponse.TransformationState
    filterIds: _containers.RepeatedScalarFieldContainer[int]
    synthetic: bool
    priming: bool
    def __init__(self, id: _Optional[int] = ..., key: _Optional[bytes] = ..., newValue: _Optional[bytes] = ..., oldValue: _Optional[bytes] = ..., transformationState: _Optional[_Union[MapEventResponse.TransformationState, str]] = ..., filterIds: _Optional[_Iterable[int]] = ..., synthetic: bool = ..., priming: bool = ...) -> None: ...

class HeartbeatMessage(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: bytes
    def __init__(self, uuid: _Optional[bytes] = ...) -> None: ...
