import common_messages_v1_pb2 as _common_messages_v1_pb2
from google.protobuf import any_pb2 as _any_pb2
from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import wrappers_pb2 as _wrappers_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class NamedCacheRequestType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    Unknown: _ClassVar[NamedCacheRequestType]
    EnsureCache: _ClassVar[NamedCacheRequestType]
    Aggregate: _ClassVar[NamedCacheRequestType]
    Clear: _ClassVar[NamedCacheRequestType]
    ContainsEntry: _ClassVar[NamedCacheRequestType]
    ContainsKey: _ClassVar[NamedCacheRequestType]
    ContainsValue: _ClassVar[NamedCacheRequestType]
    Destroy: _ClassVar[NamedCacheRequestType]
    IsEmpty: _ClassVar[NamedCacheRequestType]
    IsReady: _ClassVar[NamedCacheRequestType]
    Get: _ClassVar[NamedCacheRequestType]
    GetAll: _ClassVar[NamedCacheRequestType]
    Index: _ClassVar[NamedCacheRequestType]
    Invoke: _ClassVar[NamedCacheRequestType]
    MapListener: _ClassVar[NamedCacheRequestType]
    PageOfEntries: _ClassVar[NamedCacheRequestType]
    PageOfKeys: _ClassVar[NamedCacheRequestType]
    Put: _ClassVar[NamedCacheRequestType]
    PutAll: _ClassVar[NamedCacheRequestType]
    PutIfAbsent: _ClassVar[NamedCacheRequestType]
    QueryEntries: _ClassVar[NamedCacheRequestType]
    QueryKeys: _ClassVar[NamedCacheRequestType]
    QueryValues: _ClassVar[NamedCacheRequestType]
    Remove: _ClassVar[NamedCacheRequestType]
    RemoveMapping: _ClassVar[NamedCacheRequestType]
    Replace: _ClassVar[NamedCacheRequestType]
    ReplaceMapping: _ClassVar[NamedCacheRequestType]
    Size: _ClassVar[NamedCacheRequestType]
    Truncate: _ClassVar[NamedCacheRequestType]

class ResponseType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    Message: _ClassVar[ResponseType]
    MapEvent: _ClassVar[ResponseType]
    Destroyed: _ClassVar[ResponseType]
    Truncated: _ClassVar[ResponseType]
Unknown: NamedCacheRequestType
EnsureCache: NamedCacheRequestType
Aggregate: NamedCacheRequestType
Clear: NamedCacheRequestType
ContainsEntry: NamedCacheRequestType
ContainsKey: NamedCacheRequestType
ContainsValue: NamedCacheRequestType
Destroy: NamedCacheRequestType
IsEmpty: NamedCacheRequestType
IsReady: NamedCacheRequestType
Get: NamedCacheRequestType
GetAll: NamedCacheRequestType
Index: NamedCacheRequestType
Invoke: NamedCacheRequestType
MapListener: NamedCacheRequestType
PageOfEntries: NamedCacheRequestType
PageOfKeys: NamedCacheRequestType
Put: NamedCacheRequestType
PutAll: NamedCacheRequestType
PutIfAbsent: NamedCacheRequestType
QueryEntries: NamedCacheRequestType
QueryKeys: NamedCacheRequestType
QueryValues: NamedCacheRequestType
Remove: NamedCacheRequestType
RemoveMapping: NamedCacheRequestType
Replace: NamedCacheRequestType
ReplaceMapping: NamedCacheRequestType
Size: NamedCacheRequestType
Truncate: NamedCacheRequestType
Message: ResponseType
MapEvent: ResponseType
Destroyed: ResponseType
Truncated: ResponseType

class NamedCacheRequest(_message.Message):
    __slots__ = ("type", "cacheId", "message")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    CACHEID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    type: NamedCacheRequestType
    cacheId: int
    message: _any_pb2.Any
    def __init__(self, type: _Optional[_Union[NamedCacheRequestType, str]] = ..., cacheId: _Optional[int] = ..., message: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...

class NamedCacheResponse(_message.Message):
    __slots__ = ("cacheId", "type", "message")
    CACHEID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    cacheId: int
    type: ResponseType
    message: _any_pb2.Any
    def __init__(self, cacheId: _Optional[int] = ..., type: _Optional[_Union[ResponseType, str]] = ..., message: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...

class EnsureCacheRequest(_message.Message):
    __slots__ = ("cache",)
    CACHE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    def __init__(self, cache: _Optional[str] = ...) -> None: ...

class PutRequest(_message.Message):
    __slots__ = ("key", "value", "ttl")
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    TTL_FIELD_NUMBER: _ClassVar[int]
    key: bytes
    value: bytes
    ttl: int
    def __init__(self, key: _Optional[bytes] = ..., value: _Optional[bytes] = ..., ttl: _Optional[int] = ...) -> None: ...

class PutAllRequest(_message.Message):
    __slots__ = ("entries", "ttl")
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    TTL_FIELD_NUMBER: _ClassVar[int]
    entries: _containers.RepeatedCompositeFieldContainer[_common_messages_v1_pb2.BinaryKeyAndValue]
    ttl: int
    def __init__(self, entries: _Optional[_Iterable[_Union[_common_messages_v1_pb2.BinaryKeyAndValue, _Mapping]]] = ..., ttl: _Optional[int] = ...) -> None: ...

class ReplaceMappingRequest(_message.Message):
    __slots__ = ("key", "previousValue", "newValue")
    KEY_FIELD_NUMBER: _ClassVar[int]
    PREVIOUSVALUE_FIELD_NUMBER: _ClassVar[int]
    NEWVALUE_FIELD_NUMBER: _ClassVar[int]
    key: bytes
    previousValue: bytes
    newValue: bytes
    def __init__(self, key: _Optional[bytes] = ..., previousValue: _Optional[bytes] = ..., newValue: _Optional[bytes] = ...) -> None: ...

class IndexRequest(_message.Message):
    __slots__ = ("add", "extractor", "sorted", "comparator")
    ADD_FIELD_NUMBER: _ClassVar[int]
    EXTRACTOR_FIELD_NUMBER: _ClassVar[int]
    SORTED_FIELD_NUMBER: _ClassVar[int]
    COMPARATOR_FIELD_NUMBER: _ClassVar[int]
    add: bool
    extractor: bytes
    sorted: bool
    comparator: bytes
    def __init__(self, add: bool = ..., extractor: _Optional[bytes] = ..., sorted: bool = ..., comparator: _Optional[bytes] = ...) -> None: ...

class KeysOrFilter(_message.Message):
    __slots__ = ("key", "keys", "filter")
    KEY_FIELD_NUMBER: _ClassVar[int]
    KEYS_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    key: bytes
    keys: _common_messages_v1_pb2.CollectionOfBytesValues
    filter: bytes
    def __init__(self, key: _Optional[bytes] = ..., keys: _Optional[_Union[_common_messages_v1_pb2.CollectionOfBytesValues, _Mapping]] = ..., filter: _Optional[bytes] = ...) -> None: ...

class KeyOrFilter(_message.Message):
    __slots__ = ("key", "filter")
    KEY_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    key: bytes
    filter: bytes
    def __init__(self, key: _Optional[bytes] = ..., filter: _Optional[bytes] = ...) -> None: ...

class ExecuteRequest(_message.Message):
    __slots__ = ("agent", "keys")
    AGENT_FIELD_NUMBER: _ClassVar[int]
    KEYS_FIELD_NUMBER: _ClassVar[int]
    agent: bytes
    keys: KeysOrFilter
    def __init__(self, agent: _Optional[bytes] = ..., keys: _Optional[_Union[KeysOrFilter, _Mapping]] = ...) -> None: ...

class QueryRequest(_message.Message):
    __slots__ = ("filter", "comparator")
    FILTER_FIELD_NUMBER: _ClassVar[int]
    COMPARATOR_FIELD_NUMBER: _ClassVar[int]
    filter: bytes
    comparator: bytes
    def __init__(self, filter: _Optional[bytes] = ..., comparator: _Optional[bytes] = ...) -> None: ...

class MapListenerRequest(_message.Message):
    __slots__ = ("subscribe", "keyOrFilter", "filterId", "lite", "synchronous", "priming", "trigger")
    SUBSCRIBE_FIELD_NUMBER: _ClassVar[int]
    KEYORFILTER_FIELD_NUMBER: _ClassVar[int]
    FILTERID_FIELD_NUMBER: _ClassVar[int]
    LITE_FIELD_NUMBER: _ClassVar[int]
    SYNCHRONOUS_FIELD_NUMBER: _ClassVar[int]
    PRIMING_FIELD_NUMBER: _ClassVar[int]
    TRIGGER_FIELD_NUMBER: _ClassVar[int]
    subscribe: bool
    keyOrFilter: KeyOrFilter
    filterId: int
    lite: bool
    synchronous: bool
    priming: bool
    trigger: bytes
    def __init__(self, subscribe: bool = ..., keyOrFilter: _Optional[_Union[KeyOrFilter, _Mapping]] = ..., filterId: _Optional[int] = ..., lite: bool = ..., synchronous: bool = ..., priming: bool = ..., trigger: _Optional[bytes] = ...) -> None: ...

class MapEventMessage(_message.Message):
    __slots__ = ("id", "key", "newValue", "oldValue", "transformationState", "filterIds", "synthetic", "priming", "expired", "versionUpdate")
    class TransformationState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        NON_TRANSFORMABLE: _ClassVar[MapEventMessage.TransformationState]
        TRANSFORMABLE: _ClassVar[MapEventMessage.TransformationState]
        TRANSFORMED: _ClassVar[MapEventMessage.TransformationState]
    NON_TRANSFORMABLE: MapEventMessage.TransformationState
    TRANSFORMABLE: MapEventMessage.TransformationState
    TRANSFORMED: MapEventMessage.TransformationState
    ID_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    NEWVALUE_FIELD_NUMBER: _ClassVar[int]
    OLDVALUE_FIELD_NUMBER: _ClassVar[int]
    TRANSFORMATIONSTATE_FIELD_NUMBER: _ClassVar[int]
    FILTERIDS_FIELD_NUMBER: _ClassVar[int]
    SYNTHETIC_FIELD_NUMBER: _ClassVar[int]
    PRIMING_FIELD_NUMBER: _ClassVar[int]
    EXPIRED_FIELD_NUMBER: _ClassVar[int]
    VERSIONUPDATE_FIELD_NUMBER: _ClassVar[int]
    id: int
    key: bytes
    newValue: bytes
    oldValue: bytes
    transformationState: MapEventMessage.TransformationState
    filterIds: _containers.RepeatedScalarFieldContainer[int]
    synthetic: bool
    priming: bool
    expired: bool
    versionUpdate: bool
    def __init__(self, id: _Optional[int] = ..., key: _Optional[bytes] = ..., newValue: _Optional[bytes] = ..., oldValue: _Optional[bytes] = ..., transformationState: _Optional[_Union[MapEventMessage.TransformationState, str]] = ..., filterIds: _Optional[_Iterable[int]] = ..., synthetic: bool = ..., priming: bool = ..., expired: bool = ..., versionUpdate: bool = ...) -> None: ...
