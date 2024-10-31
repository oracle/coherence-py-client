# mypy: ignore-errors
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

Aggregate: NamedCacheRequestType
Clear: NamedCacheRequestType
ContainsEntry: NamedCacheRequestType
ContainsKey: NamedCacheRequestType
ContainsValue: NamedCacheRequestType
DESCRIPTOR: _descriptor.FileDescriptor
Destroy: NamedCacheRequestType
Destroyed: ResponseType
EnsureCache: NamedCacheRequestType
Get: NamedCacheRequestType
GetAll: NamedCacheRequestType
Index: NamedCacheRequestType
Invoke: NamedCacheRequestType
IsEmpty: NamedCacheRequestType
IsReady: NamedCacheRequestType
MapEvent: ResponseType
MapListener: NamedCacheRequestType
Message: ResponseType
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
Truncated: ResponseType
Unknown: NamedCacheRequestType

class EnsureCacheRequest(_message.Message):
    __slots__ = ["cache"]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    cache: str
    def __init__(self, cache: _Optional[str] = ...) -> None: ...

class ExecuteRequest(_message.Message):
    __slots__ = ["agent", "keys"]
    AGENT_FIELD_NUMBER: _ClassVar[int]
    KEYS_FIELD_NUMBER: _ClassVar[int]
    agent: bytes
    keys: KeysOrFilter
    def __init__(self, agent: _Optional[bytes] = ..., keys: _Optional[_Union[KeysOrFilter, _Mapping]] = ...) -> None: ...

class IndexRequest(_message.Message):
    __slots__ = ["add", "comparator", "extractor", "sorted"]
    ADD_FIELD_NUMBER: _ClassVar[int]
    COMPARATOR_FIELD_NUMBER: _ClassVar[int]
    EXTRACTOR_FIELD_NUMBER: _ClassVar[int]
    SORTED_FIELD_NUMBER: _ClassVar[int]
    add: bool
    comparator: bytes
    extractor: bytes
    sorted: bool
    def __init__(self, add: bool = ..., extractor: _Optional[bytes] = ..., sorted: bool = ..., comparator: _Optional[bytes] = ...) -> None: ...

class KeyOrFilter(_message.Message):
    __slots__ = ["filter", "key"]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    filter: bytes
    key: bytes
    def __init__(self, key: _Optional[bytes] = ..., filter: _Optional[bytes] = ...) -> None: ...

class KeysOrFilter(_message.Message):
    __slots__ = ["filter", "key", "keys"]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    KEYS_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    filter: bytes
    key: bytes
    keys: _common_messages_v1_pb2.CollectionOfBytesValues
    def __init__(self, key: _Optional[bytes] = ..., keys: _Optional[_Union[_common_messages_v1_pb2.CollectionOfBytesValues, _Mapping]] = ..., filter: _Optional[bytes] = ...) -> None: ...

class MapEventMessage(_message.Message):
    __slots__ = ["expired", "filterIds", "id", "key", "newValue", "oldValue", "priming", "synthetic", "transformationState", "versionUpdate"]
    class TransformationState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    EXPIRED_FIELD_NUMBER: _ClassVar[int]
    FILTERIDS_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    NEWVALUE_FIELD_NUMBER: _ClassVar[int]
    NON_TRANSFORMABLE: MapEventMessage.TransformationState
    OLDVALUE_FIELD_NUMBER: _ClassVar[int]
    PRIMING_FIELD_NUMBER: _ClassVar[int]
    SYNTHETIC_FIELD_NUMBER: _ClassVar[int]
    TRANSFORMABLE: MapEventMessage.TransformationState
    TRANSFORMATIONSTATE_FIELD_NUMBER: _ClassVar[int]
    TRANSFORMED: MapEventMessage.TransformationState
    VERSIONUPDATE_FIELD_NUMBER: _ClassVar[int]
    expired: bool
    filterIds: _containers.RepeatedScalarFieldContainer[int]
    id: int
    key: bytes
    newValue: bytes
    oldValue: bytes
    priming: bool
    synthetic: bool
    transformationState: MapEventMessage.TransformationState
    versionUpdate: bool
    def __init__(self, id: _Optional[int] = ..., key: _Optional[bytes] = ..., newValue: _Optional[bytes] = ..., oldValue: _Optional[bytes] = ..., transformationState: _Optional[_Union[MapEventMessage.TransformationState, str]] = ..., filterIds: _Optional[_Iterable[int]] = ..., synthetic: bool = ..., priming: bool = ..., expired: bool = ..., versionUpdate: bool = ...) -> None: ...

class MapListenerRequest(_message.Message):
    __slots__ = ["filterId", "keyOrFilter", "lite", "priming", "subscribe", "synchronous", "trigger"]
    FILTERID_FIELD_NUMBER: _ClassVar[int]
    KEYORFILTER_FIELD_NUMBER: _ClassVar[int]
    LITE_FIELD_NUMBER: _ClassVar[int]
    PRIMING_FIELD_NUMBER: _ClassVar[int]
    SUBSCRIBE_FIELD_NUMBER: _ClassVar[int]
    SYNCHRONOUS_FIELD_NUMBER: _ClassVar[int]
    TRIGGER_FIELD_NUMBER: _ClassVar[int]
    filterId: int
    keyOrFilter: KeyOrFilter
    lite: bool
    priming: bool
    subscribe: bool
    synchronous: bool
    trigger: bytes
    def __init__(self, subscribe: bool = ..., keyOrFilter: _Optional[_Union[KeyOrFilter, _Mapping]] = ..., filterId: _Optional[int] = ..., lite: bool = ..., synchronous: bool = ..., priming: bool = ..., trigger: _Optional[bytes] = ...) -> None: ...

class NamedCacheRequest(_message.Message):
    __slots__ = ["cacheId", "message", "type"]
    CACHEID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    cacheId: int
    message: _any_pb2.Any
    type: NamedCacheRequestType
    def __init__(self, type: _Optional[_Union[NamedCacheRequestType, str]] = ..., cacheId: _Optional[int] = ..., message: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...

class NamedCacheResponse(_message.Message):
    __slots__ = ["cacheId", "message", "type"]
    CACHEID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    cacheId: int
    message: _any_pb2.Any
    type: ResponseType
    def __init__(self, cacheId: _Optional[int] = ..., type: _Optional[_Union[ResponseType, str]] = ..., message: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...

class PutAllRequest(_message.Message):
    __slots__ = ["entries", "ttl"]
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    TTL_FIELD_NUMBER: _ClassVar[int]
    entries: _containers.RepeatedCompositeFieldContainer[_common_messages_v1_pb2.BinaryKeyAndValue]
    ttl: int
    def __init__(self, entries: _Optional[_Iterable[_Union[_common_messages_v1_pb2.BinaryKeyAndValue, _Mapping]]] = ..., ttl: _Optional[int] = ...) -> None: ...

class PutRequest(_message.Message):
    __slots__ = ["key", "ttl", "value"]
    KEY_FIELD_NUMBER: _ClassVar[int]
    TTL_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: bytes
    ttl: int
    value: bytes
    def __init__(self, key: _Optional[bytes] = ..., value: _Optional[bytes] = ..., ttl: _Optional[int] = ...) -> None: ...

class QueryRequest(_message.Message):
    __slots__ = ["comparator", "filter"]
    COMPARATOR_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    comparator: bytes
    filter: bytes
    def __init__(self, filter: _Optional[bytes] = ..., comparator: _Optional[bytes] = ...) -> None: ...

class ReplaceMappingRequest(_message.Message):
    __slots__ = ["key", "newValue", "previousValue"]
    KEY_FIELD_NUMBER: _ClassVar[int]
    NEWVALUE_FIELD_NUMBER: _ClassVar[int]
    PREVIOUSVALUE_FIELD_NUMBER: _ClassVar[int]
    key: bytes
    newValue: bytes
    previousValue: bytes
    def __init__(self, key: _Optional[bytes] = ..., previousValue: _Optional[bytes] = ..., newValue: _Optional[bytes] = ...) -> None: ...

class NamedCacheRequestType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class ResponseType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
