# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.
from coherence import Extractors, Filters
from coherence.ai import (
    BinaryQueryResult,
    BitVector,
    ByteVector,
    CosineDistance,
    DocumentChunk,
    FloatVector,
    SimilaritySearch,
)
from coherence.extractor import ValueExtractor
from coherence.filter import Filter
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
    assert ser == (
        b'\x15{"@class": "ai.DocumentChunk", "dataVersion": 0, '
        b'"metadata": {"@ordered": true, "entries": []}, "text": "test"}'
    )
    o = s.deserialize(ser)
    assert isinstance(o, DocumentChunk)

    d = {"one": "one-value", "two": "two-value"}
    dc = DocumentChunk("test", d)
    ser = s.serialize(dc)
    assert ser == (
        b'\x15{"@class": "ai.DocumentChunk", "dataVersion": 0, "metadata": {"entries": ['
        b'{"key": "one", "value": "one-value"}, {"key": "two", "value": "two-value"}]}, '
        b'"text": "test"}'
    )
    o = s.deserialize(ser)
    assert isinstance(o, DocumentChunk)

    coh_fv = FloatVector([1.0, 2.0, 3.0])
    d = {"one": "one-value", "two": "two-value"}
    dc = DocumentChunk("test", d, coh_fv)
    ser = s.serialize(dc)
    assert ser == (
        b'\x15{"@class": "ai.DocumentChunk", "dataVersion": 0, "metadata": {"entries": ['
        b'{"key": "one", "value": "one-value"}, {"key": "two", "value": "two-value"}]}, '
        b'"vector": {"@class": "ai.Float32Vector", "array": [1.0, 2.0, 3.0]}, "text": "test"}'
    )
    o = s.deserialize(ser)
    assert isinstance(o, DocumentChunk)


# noinspection PyUnresolvedReferences
def test_SimilaritySearch_serialization() -> None:
    coh_fv = FloatVector([1.0, 2.0, 3.0])
    ve = Extractors.extract("foo")
    f = Filters.equals("foo", "bar")
    ss = SimilaritySearch(ve, coh_fv, 19, filter=f)
    ser = s.serialize(ss)
    assert ser == (
        b'\x15{"@class": "ai.search.SimilarityAggregator", '
        b'"extractor": {"@class": "extractor.UniversalExtractor", "name": "foo", "params": null}, '
        b'"algorithm": {"@class": "ai.distance.CosineSimilarity"}, '
        b'"bruteForce": true, '
        b'"filter": {"@class": "filter.EqualsFilter", '
        b'"extractor": {"@class": "extractor.UniversalExtractor", '
        b'"name": "foo", "params": null}, "value": "bar"}, "maxResults": 19, '
        b'"vector": {"@class": "ai.Float32Vector", "array": [1.0, 2.0, 3.0]}}'
    )

    o = s.deserialize(ser)
    assert isinstance(o, SimilaritySearch)
    assert isinstance(o.extractor, ValueExtractor)
    assert isinstance(o.algorithm, CosineDistance)
    assert isinstance(o.filter, Filter)
    assert o.maxResults == 19
    assert isinstance(o.vector, FloatVector)


# noinspection PyUnresolvedReferences
def test_BinaryQueryResult_serialization() -> None:
    bqr = BinaryQueryResult(3.0, 1, "abc")
    ser = s.serialize(bqr)
    assert ser == b'\x15{"@class": "ai.results.BinaryQueryResult", "distance": 3.0, "key": 1, "value": "abc"}'

    o = s.deserialize(ser)
    assert isinstance(o, BinaryQueryResult)
    assert o.distance == 3.0
    assert o.key == 1
    assert o.value == "abc"
