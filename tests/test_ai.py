# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from coherence.ai import BitVector, ByteVector, FloatVector, DocumentChunk
from coherence.serialization import JSONSerializer, SerializerRegistry

s = SerializerRegistry.serializer(JSONSerializer.SER_FORMAT)


def test_BitVector_serialization() -> None:
    coh_bv = BitVector(hex_string="AABBCC")
    ser = s.serialize(coh_bv)
    assert ser == b'\x15{"@class": "ai.BitVector", "bits": "0xAABBCC"}'
    o = s.deserialize(ser)
    assert isinstance(o, BitVector)

    coh_bv = BitVector(hex_string="0xAABBCC")
    ser = s.serialize(coh_bv)
    assert ser == b'\x15{"@class": "ai.BitVector", "bits": "0xAABBCC"}'
    o = s.deserialize(ser)
    assert isinstance(o, BitVector)

    coh_bv = BitVector(hex_string=None, byte_array=bytes([1, 2, 10]))
    ser = s.serialize(coh_bv)
    assert ser == b'\x15{"@class": "ai.BitVector", "bits": "0x01020a"}'
    o = s.deserialize(ser)
    assert isinstance(o, BitVector)

    coh_bv = BitVector(hex_string=None, int_array=[1234, 1235])
    ser = s.serialize(coh_bv)
    assert ser == b'\x15{"@class": "ai.BitVector", "bits": "0x4d24d3"}'
    o = s.deserialize(ser)
    assert isinstance(o, BitVector)


def test_ByteVector_serialization() -> None:
    coh_int8v = ByteVector(bytes([1, 2, 3, 4]))
    ser = s.serialize(coh_int8v)
    assert ser == b'\x15{"@class": "ai.Int8Vector", "array": "AQIDBA=="}'
    o = s.deserialize(ser)
    assert isinstance(o, ByteVector)


def test_FloatVector_serialization() -> None:
    coh_fv = FloatVector([1.0, 2.0, 3.0])
    ser = s.serialize(coh_fv)
    assert ser == b'\x15{"@class": "ai.Float32Vector", "array": [1.0, 2.0, 3.0]}'
    o = s.deserialize(ser)
    assert isinstance(o, FloatVector)


def test_DocumentChunk_serialization() -> None:
    dc = DocumentChunk("test")
    ser = s.serialize(dc)
    assert ser == b'\x15{"@class": "ai.DocumentChunk", "dataVersion": 0, "metadata": {"@ordered": true, "entries": []}, "text": "test"}'
    o = s.deserialize(ser)
    assert isinstance(o, DocumentChunk)

    d = {"one":"one-value", "two": "two-value"}
    dc = DocumentChunk("test",d)
    ser = s.serialize(dc)
    assert ser == b'\x15{"@class": "ai.DocumentChunk", "dataVersion": 0, "metadata": {"entries": [{"key": "one", "value": "one-value"}, {"key": "two", "value": "two-value"}]}, "text": "test"}'
    o = s.deserialize(ser)
    assert isinstance(o, DocumentChunk)

    coh_fv = FloatVector([1.0, 2.0, 3.0])
    d = {"one":"one-value", "two": "two-value"}
    dc = DocumentChunk("test",d, coh_fv)
    ser = s.serialize(dc)
    assert ser == b'\x15{"@class": "ai.DocumentChunk", "dataVersion": 0, "metadata": {"entries": [{"key": "one", "value": "one-value"}, {"key": "two", "value": "two-value"}]}, "vector": {"@class": "ai.Float32Vector", "array": [1.0, 2.0, 3.0]}, "text": "test"}'
    o = s.deserialize(ser)
    assert isinstance(o, DocumentChunk)

