# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: common_messages_v1.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x18\x63ommon_messages_v1.proto\x12\x13\x63oherence.common.v1\x1a\x19google/protobuf/any.proto\"=\n\x0c\x45rrorMessage\x12\x0f\n\x07message\x18\x01 \x01(\t\x12\x12\n\x05\x65rror\x18\x02 \x01(\x0cH\x00\x88\x01\x01\x42\x08\n\x06_error\"\n\n\x08\x43omplete\";\n\x10HeartbeatMessage\x12\x11\n\x04uuid\x18\x01 \x01(\x0cH\x00\x88\x01\x01\x12\x0b\n\x03\x61\x63k\x18\x02 \x01(\x08\x42\x07\n\x05_uuid\"/\n\rOptionalValue\x12\x0f\n\x07present\x18\x01 \x01(\x08\x12\r\n\x05value\x18\x02 \x01(\x0c\")\n\x17\x43ollectionOfBytesValues\x12\x0e\n\x06values\x18\x01 \x03(\x0c\"/\n\x11\x42inaryKeyAndValue\x12\x0b\n\x03key\x18\x01 \x01(\x0c\x12\r\n\x05value\x18\x02 \x01(\x0c\x42\x30\n,com.oracle.coherence.grpc.messages.common.v1P\x01\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'common_messages_v1_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'\n,com.oracle.coherence.grpc.messages.common.v1P\001'
  _ERRORMESSAGE._serialized_start=76
  _ERRORMESSAGE._serialized_end=137
  _COMPLETE._serialized_start=139
  _COMPLETE._serialized_end=149
  _HEARTBEATMESSAGE._serialized_start=151
  _HEARTBEATMESSAGE._serialized_end=210
  _OPTIONALVALUE._serialized_start=212
  _OPTIONALVALUE._serialized_end=259
  _COLLECTIONOFBYTESVALUES._serialized_start=261
  _COLLECTIONOFBYTESVALUES._serialized_end=302
  _BINARYKEYANDVALUE._serialized_start=304
  _BINARYKEYANDVALUE._serialized_end=351
# @@protoc_insertion_point(module_scope)