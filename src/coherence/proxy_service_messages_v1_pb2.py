# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: proxy_service_messages_v1.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import coherence.common_messages_v1_pb2 as common__messages__v1__pb2
from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1fproxy_service_messages_v1.proto\x12\x12\x63oherence.proxy.v1\x1a\x18\x63ommon_messages_v1.proto\x1a\x19google/protobuf/any.proto\"\xbb\x01\n\x0cProxyRequest\x12\n\n\x02id\x18\x01 \x01(\x03\x12/\n\x04init\x18\x03 \x01(\x0b\x32\x1f.coherence.proxy.v1.InitRequestH\x00\x12\'\n\x07message\x18\x04 \x01(\x0b\x32\x14.google.protobuf.AnyH\x00\x12:\n\theartbeat\x18\x05 \x01(\x0b\x32%.coherence.common.v1.HeartbeatMessageH\x00\x42\t\n\x07request\"\xa5\x02\n\rProxyResponse\x12\n\n\x02id\x18\x01 \x01(\x03\x12\x30\n\x04init\x18\x04 \x01(\x0b\x32 .coherence.proxy.v1.InitResponseH\x00\x12\'\n\x07message\x18\x05 \x01(\x0b\x32\x14.google.protobuf.AnyH\x00\x12\x32\n\x05\x65rror\x18\x06 \x01(\x0b\x32!.coherence.common.v1.ErrorMessageH\x00\x12\x31\n\x08\x63omplete\x18\x07 \x01(\x0b\x32\x1d.coherence.common.v1.CompleteH\x00\x12:\n\theartbeat\x18\x08 \x01(\x0b\x32%.coherence.common.v1.HeartbeatMessageH\x00\x42\n\n\x08response\"\xc7\x01\n\x0bInitRequest\x12\r\n\x05scope\x18\x02 \x01(\t\x12\x0e\n\x06\x66ormat\x18\x03 \x01(\t\x12\x10\n\x08protocol\x18\x04 \x01(\t\x12\x17\n\x0fprotocolVersion\x18\x05 \x01(\x05\x12 \n\x18supportedProtocolVersion\x18\x06 \x01(\x05\x12\x16\n\theartbeat\x18\x07 \x01(\x03H\x00\x88\x01\x01\x12\x17\n\nclientUuid\x18\x08 \x01(\x0cH\x01\x88\x01\x01\x42\x0c\n\n_heartbeatB\r\n\x0b_clientUuid\"\x8e\x01\n\x0cInitResponse\x12\x0c\n\x04uuid\x18\x01 \x01(\x0c\x12\x0f\n\x07version\x18\x02 \x01(\t\x12\x16\n\x0e\x65ncodedVersion\x18\x03 \x01(\x05\x12\x17\n\x0fprotocolVersion\x18\x04 \x01(\x05\x12\x15\n\rproxyMemberId\x18\x05 \x01(\x05\x12\x17\n\x0fproxyMemberUuid\x18\x06 \x01(\x0c\x42/\n+com.oracle.coherence.grpc.messages.proxy.v1P\x01\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'proxy_service_messages_v1_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'\n+com.oracle.coherence.grpc.messages.proxy.v1P\001'
  _PROXYREQUEST._serialized_start=109
  _PROXYREQUEST._serialized_end=296
  _PROXYRESPONSE._serialized_start=299
  _PROXYRESPONSE._serialized_end=592
  _INITREQUEST._serialized_start=595
  _INITREQUEST._serialized_end=794
  _INITRESPONSE._serialized_start=797
  _INITRESPONSE._serialized_end=939
# @@protoc_insertion_point(module_scope)