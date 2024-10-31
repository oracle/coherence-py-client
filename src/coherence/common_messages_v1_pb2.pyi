# mypy: ignore-errors
from google.protobuf import any_pb2 as _any_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class BinaryKeyAndValue(_message.Message):
    __slots__ = ["key", "value"]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: bytes
    value: bytes
    def __init__(self, key: _Optional[bytes] = ..., value: _Optional[bytes] = ...) -> None: ...

class CollectionOfBytesValues(_message.Message):
    __slots__ = ["values"]
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[bytes]
    def __init__(self, values: _Optional[_Iterable[bytes]] = ...) -> None: ...

class Complete(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class ErrorMessage(_message.Message):
    __slots__ = ["error", "message"]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    error: bytes
    message: str
    def __init__(self, message: _Optional[str] = ..., error: _Optional[bytes] = ...) -> None: ...

class HeartbeatMessage(_message.Message):
    __slots__ = ["ack", "uuid"]
    ACK_FIELD_NUMBER: _ClassVar[int]
    UUID_FIELD_NUMBER: _ClassVar[int]
    ack: bool
    uuid: bytes
    def __init__(self, uuid: _Optional[bytes] = ..., ack: bool = ...) -> None: ...

class OptionalValue(_message.Message):
    __slots__ = ["present", "value"]
    PRESENT_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    present: bool
    value: bytes
    def __init__(self, present: bool = ..., value: _Optional[bytes] = ...) -> None: ...
