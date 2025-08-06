import common_messages_v1_pb2 as _common_messages_v1_pb2
from google.protobuf import any_pb2 as _any_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ProxyRequest(_message.Message):
    __slots__ = ("id", "init", "message", "heartbeat", "context")
    class ContextEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _any_pb2.Any
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    INIT_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    HEARTBEAT_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    id: int
    init: InitRequest
    message: _any_pb2.Any
    heartbeat: _common_messages_v1_pb2.HeartbeatMessage
    context: _containers.MessageMap[str, _any_pb2.Any]
    def __init__(self, id: _Optional[int] = ..., init: _Optional[_Union[InitRequest, _Mapping]] = ..., message: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., heartbeat: _Optional[_Union[_common_messages_v1_pb2.HeartbeatMessage, _Mapping]] = ..., context: _Optional[_Mapping[str, _any_pb2.Any]] = ...) -> None: ...

class ProxyResponse(_message.Message):
    __slots__ = ("id", "init", "message", "error", "complete", "heartbeat", "context")
    class ContextEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _any_pb2.Any
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    INIT_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    COMPLETE_FIELD_NUMBER: _ClassVar[int]
    HEARTBEAT_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    id: int
    init: InitResponse
    message: _any_pb2.Any
    error: _common_messages_v1_pb2.ErrorMessage
    complete: _common_messages_v1_pb2.Complete
    heartbeat: _common_messages_v1_pb2.HeartbeatMessage
    context: _containers.MessageMap[str, _any_pb2.Any]
    def __init__(self, id: _Optional[int] = ..., init: _Optional[_Union[InitResponse, _Mapping]] = ..., message: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., error: _Optional[_Union[_common_messages_v1_pb2.ErrorMessage, _Mapping]] = ..., complete: _Optional[_Union[_common_messages_v1_pb2.Complete, _Mapping]] = ..., heartbeat: _Optional[_Union[_common_messages_v1_pb2.HeartbeatMessage, _Mapping]] = ..., context: _Optional[_Mapping[str, _any_pb2.Any]] = ...) -> None: ...

class InitRequest(_message.Message):
    __slots__ = ("scope", "format", "protocol", "protocolVersion", "supportedProtocolVersion", "heartbeat", "clientUuid", "identity")
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    PROTOCOL_FIELD_NUMBER: _ClassVar[int]
    PROTOCOLVERSION_FIELD_NUMBER: _ClassVar[int]
    SUPPORTEDPROTOCOLVERSION_FIELD_NUMBER: _ClassVar[int]
    HEARTBEAT_FIELD_NUMBER: _ClassVar[int]
    CLIENTUUID_FIELD_NUMBER: _ClassVar[int]
    IDENTITY_FIELD_NUMBER: _ClassVar[int]
    scope: str
    format: str
    protocol: str
    protocolVersion: int
    supportedProtocolVersion: int
    heartbeat: int
    clientUuid: bytes
    identity: ClientMemberIdentity
    def __init__(self, scope: _Optional[str] = ..., format: _Optional[str] = ..., protocol: _Optional[str] = ..., protocolVersion: _Optional[int] = ..., supportedProtocolVersion: _Optional[int] = ..., heartbeat: _Optional[int] = ..., clientUuid: _Optional[bytes] = ..., identity: _Optional[_Union[ClientMemberIdentity, _Mapping]] = ...) -> None: ...

class InitResponse(_message.Message):
    __slots__ = ("uuid", "version", "encodedVersion", "protocolVersion", "proxyMemberId", "proxyMemberUuid")
    UUID_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    ENCODEDVERSION_FIELD_NUMBER: _ClassVar[int]
    PROTOCOLVERSION_FIELD_NUMBER: _ClassVar[int]
    PROXYMEMBERID_FIELD_NUMBER: _ClassVar[int]
    PROXYMEMBERUUID_FIELD_NUMBER: _ClassVar[int]
    uuid: bytes
    version: str
    encodedVersion: int
    protocolVersion: int
    proxyMemberId: int
    proxyMemberUuid: bytes
    def __init__(self, uuid: _Optional[bytes] = ..., version: _Optional[str] = ..., encodedVersion: _Optional[int] = ..., protocolVersion: _Optional[int] = ..., proxyMemberId: _Optional[int] = ..., proxyMemberUuid: _Optional[bytes] = ...) -> None: ...

class ClientMemberIdentity(_message.Message):
    __slots__ = ("clusterName", "machineId", "machineName", "memberName", "priority", "processName", "rackName", "siteName", "roleName")
    CLUSTERNAME_FIELD_NUMBER: _ClassVar[int]
    MACHINEID_FIELD_NUMBER: _ClassVar[int]
    MACHINENAME_FIELD_NUMBER: _ClassVar[int]
    MEMBERNAME_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    PROCESSNAME_FIELD_NUMBER: _ClassVar[int]
    RACKNAME_FIELD_NUMBER: _ClassVar[int]
    SITENAME_FIELD_NUMBER: _ClassVar[int]
    ROLENAME_FIELD_NUMBER: _ClassVar[int]
    clusterName: str
    machineId: int
    machineName: str
    memberName: str
    priority: int
    processName: str
    rackName: str
    siteName: str
    roleName: str
    def __init__(self, clusterName: _Optional[str] = ..., machineId: _Optional[int] = ..., machineName: _Optional[str] = ..., memberName: _Optional[str] = ..., priority: _Optional[int] = ..., processName: _Optional[str] = ..., rackName: _Optional[str] = ..., siteName: _Optional[str] = ..., roleName: _Optional[str] = ...) -> None: ...
