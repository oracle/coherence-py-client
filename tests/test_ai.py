# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from coherence.ai import BitVector, ByteVector, FloatVector
from coherence.serialization import JSONSerializer, SerializerRegistry

s = SerializerRegistry.serializer(JSONSerializer.SER_FORMAT)


def test_BitVector_serialization() -> None:
    coh_bv = BitVector(hex_string="AABBCC")
    ser = s.serialize(coh_bv)
    assert ser == b'\x15{"@class": "ai.BitVector", "bits": "0xAABBCC"}'

    coh_bv = BitVector(hex_string="0xAABBCC")
    ser = s.serialize(coh_bv)
    assert ser == b'\x15{"@class": "ai.BitVector", "bits": "0xAABBCC"}'

    coh_bv = BitVector(hex_string=None, byte_array=bytes([1, 2, 10]))
    ser = s.serialize(coh_bv)
    assert ser == b'\x15{"@class": "ai.BitVector", "bits": "0x01020a"}'

    coh_bv = BitVector(hex_string=None, int_array=[1234, 1235])
    ser = s.serialize(coh_bv)
    assert ser == b'\x15{"@class": "ai.BitVector", "bits": "0x4d24d3"}'


def test_ByteVector_serialization() -> None:
    coh_int8v = ByteVector(bytes([1, 2, 3, 4]))
    ser = s.serialize(coh_int8v)
    assert ser == b'\x15{"@class": "ai.Int8Vector", "array": "AQIDBA=="}'


def test_FloatVector_serialization() -> None:
    coh_fv = FloatVector([1.0, 2.0, 3.0])
    ser = s.serialize(coh_fv)
    assert ser == b'\x15{"@class": "ai.Float32Vector", "array": [1.0, 2.0, 3.0]}'
