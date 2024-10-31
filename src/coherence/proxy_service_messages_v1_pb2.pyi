# mypy: ignore-errors
import common_messages_v1_pb2 as _common_messages_v1_pb2
from google.protobuf import any_pb2 as _any_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class InitRequest(_message.Message):
    __slots__ = ["clientUuid", "format", "heartbeat", "protocol", "protocolVersion", "scope", "supportedProtocolVersion"]
    CLIENTUUID_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    HEARTBEAT_FIELD_NUMBER: _ClassVar[int]
    PROTOCOLVERSION_FIELD_NUMBER: _ClassVar[int]
    PROTOCOL_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    SUPPORTEDPROTOCOLVERSION_FIELD_NUMBER: _ClassVar[int]
    clientUuid: bytes
    format: str
    heartbeat: int
    protocol: str
    protocolVersion: int
    scope: str
    supportedProtocolVersion: int
    def __init__(self, scope: _Optional[str] = ..., format: _Optional[str] = ..., protocol: _Optional[str] = ..., protocolVersion: _Optional[int] = ..., supportedProtocolVersion: _Optional[int] = ..., heartbeat: _Optional[int] = ..., clientUuid: _Optional[bytes] = ...) -> None: ...

class InitResponse(_message.Message):
    __slots__ = ["encodedVersion", "protocolVersion", "proxyMemberId", "proxyMemberUuid", "uuid", "version"]
    ENCODEDVERSION_FIELD_NUMBER: _ClassVar[int]
    PROTOCOLVERSION_FIELD_NUMBER: _ClassVar[int]
    PROXYMEMBERID_FIELD_NUMBER: _ClassVar[int]
    PROXYMEMBERUUID_FIELD_NUMBER: _ClassVar[int]
    UUID_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    encodedVersion: int
    protocolVersion: int
    proxyMemberId: int
    proxyMemberUuid: bytes
    uuid: bytes
    version: str
    def __init__(self, uuid: _Optional[bytes] = ..., version: _Optional[str] = ..., encodedVersion: _Optional[int] = ..., protocolVersion: _Optional[int] = ..., proxyMemberId: _Optional[int] = ..., proxyMemberUuid: _Optional[bytes] = ...) -> None: ...

class ProxyRequest(_message.Message):
    __slots__ = ["heartbeat", "id", "init", "message"]
    HEARTBEAT_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    INIT_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    heartbeat: _common_messages_v1_pb2.HeartbeatMessage
    id: int
    init: InitRequest
    message: _any_pb2.Any
    def __init__(self, id: _Optional[int] = ..., init: _Optional[_Union[InitRequest, _Mapping]] = ..., message: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., heartbeat: _Optional[_Union[_common_messages_v1_pb2.HeartbeatMessage, _Mapping]] = ...) -> None: ...

class ProxyResponse(_message.Message):
    __slots__ = ["complete", "error", "heartbeat", "id", "init", "message"]
    COMPLETE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    HEARTBEAT_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    INIT_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    complete: _common_messages_v1_pb2.Complete
    error: _common_messages_v1_pb2.ErrorMessage
    heartbeat: _common_messages_v1_pb2.HeartbeatMessage
    id: int
    init: InitResponse
    message: _any_pb2.Any
    def __init__(self, id: _Optional[int] = ..., init: _Optional[_Union[InitResponse, _Mapping]] = ..., message: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., error: _Optional[_Union[_common_messages_v1_pb2.ErrorMessage, _Mapping]] = ..., complete: _Optional[_Union[_common_messages_v1_pb2.Complete, _Mapping]] = ..., heartbeat: _Optional[_Union[_common_messages_v1_pb2.HeartbeatMessage, _Mapping]] = ...) -> None: ...
