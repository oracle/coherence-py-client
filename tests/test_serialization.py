# Copyright (c) 2022, 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from decimal import Decimal
from typing import Any

from coherence.ai import (
    BinaryQuantIndex,
    BitVector,
    ByteVector,
    CosineDistance,
    DocumentChunk,
    FloatVector,
    QueryResult,
    SimilaritySearch,
)
from coherence.extractor import Extractors, ValueExtractor
from coherence.filter import Filter, Filters
from coherence.serialization import JSONSerializer, proxy
from tests.Task import Task


def test_python_decimal() -> None:
    _verify_round_trip(Decimal("12.1345797249237923423872493"), True)


def test_python_large_integer() -> None:
    _verify_round_trip(9223372036854775810, True)  # larger than Java Long (2^63 - 1)


def test_python_large_negative_integer() -> None:
    _verify_round_trip(-9223372036854775810, True)  # less than Java Long -2^63


def test_python_java_long_upper_bound() -> None:
    _verify_round_trip(9223372036854775807, False)  # Java Long (2^32 - 1)


def test_python_java_long_lower_bound() -> None:
    _verify_round_trip(-9223372036854775809, False)  # Java Long (2^32 - 1)


def test_custom_object() -> None:
    _verify_round_trip(Task("Milk, eggs, and bread"), True)


def test_python_numerics_in_object() -> None:
    _verify_round_trip(Simple(), False)


@proxy("test.Simple")
class Simple:
    def __init__(self) -> None:
        super().__init__()
        self.n1 = (2**63) - 1
        self.n2 = self.n1 + 5
        self.n3 = Decimal("12.1345797249237923423872493")

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Simple):
            return self.n1 == getattr(o, "n1") and self.n2 == getattr(o, "n2") and self.n3 == getattr(o, "n3")

        return False


def _verify_round_trip(obj: Any, should_have_class: bool) -> None:
    serializer: JSONSerializer = JSONSerializer()
    ser_result: bytes = serializer.serialize(obj)
    print(f"Serialized [{type(obj)}] result: {ser_result.decode()}")

    if should_have_class:
        assert "@class" in ser_result.decode()

    deser_result: Any = serializer.deserialize(ser_result)
    print(f"Deserialized [{type(deser_result)}] result: {deser_result}")
    assert deser_result == obj


def test_BitVector_serialization() -> None:
    serializer: JSONSerializer = JSONSerializer()
    coh_bv = BitVector(hex_string="AABBCC")
    ser = serializer.serialize(coh_bv)
    assert ser == b'\x15{"@class": "ai.BitVector", "bits": "0xAABBCC"}'
    o = serializer.deserialize(ser)
    assert isinstance(o, BitVector)

    coh_bv = BitVector(hex_string="0xAABBCC")
    ser = serializer.serialize(coh_bv)
    assert ser == b'\x15{"@class": "ai.BitVector", "bits": "0xAABBCC"}'
    o = serializer.deserialize(ser)
    assert isinstance(o, BitVector)

    coh_bv = BitVector(hex_string=None, byte_array=bytes([1, 2, 10]))
    ser = serializer.serialize(coh_bv)
    assert ser == b'\x15{"@class": "ai.BitVector", "bits": "0x01020a"}'
    o = serializer.deserialize(ser)
    assert isinstance(o, BitVector)

    coh_bv = BitVector(hex_string=None, int_array=[1234, 1235])
    ser = serializer.serialize(coh_bv)
    assert ser == b'\x15{"@class": "ai.BitVector", "bits": "0x4d24d3"}'
    o = serializer.deserialize(ser)
    assert isinstance(o, BitVector)


def test_ByteVector_serialization() -> None:
    serializer: JSONSerializer = JSONSerializer()
    coh_int8v = ByteVector(bytes([1, 2, 3, 4]))
    ser = serializer.serialize(coh_int8v)
    assert ser == b'\x15{"@class": "ai.Int8Vector", "array": "AQIDBA=="}'
    o = serializer.deserialize(ser)
    assert isinstance(o, ByteVector)


def test_FloatVector_serialization() -> None:
    serializer: JSONSerializer = JSONSerializer()
    coh_fv = FloatVector([1.0, 2.0, 3.0])
    ser = serializer.serialize(coh_fv)
    assert ser == b'\x15{"@class": "ai.Float32Vector", "array": [1.0, 2.0, 3.0]}'
    o = serializer.deserialize(ser)
    assert isinstance(o, FloatVector)


def test_DocumentChunk_serialization() -> None:
    serializer: JSONSerializer = JSONSerializer()
    dc = DocumentChunk("test")
    ser = serializer.serialize(dc)
    assert ser == (
        b'\x15{"@class": "ai.DocumentChunk", "dataVersion": 0, '
        b'"metadata": {"@ordered": true, "entries": []}, "text": "test"}'
    )
    o = serializer.deserialize(ser)
    assert isinstance(o, DocumentChunk)

    d = {"one": "one-value", "two": "two-value"}
    dc = DocumentChunk("test", d)
    ser = serializer.serialize(dc)
    assert ser == (
        b'\x15{"@class": "ai.DocumentChunk", "dataVersion": 0, "metadata": {"entries": ['
        b'{"key": "one", "value": "one-value"}, {"key": "two", "value": "two-value"}]}, '
        b'"text": "test"}'
    )
    o = serializer.deserialize(ser)
    assert isinstance(o, DocumentChunk)

    coh_fv = FloatVector([1.0, 2.0, 3.0])
    d = {"one": "one-value", "two": "two-value"}
    dc = DocumentChunk("test", d, coh_fv)
    ser = serializer.serialize(dc)
    assert ser == (
        b'\x15{"@class": "ai.DocumentChunk", "dataVersion": 0, "metadata": {"entries": ['
        b'{"key": "one", "value": "one-value"}, {"key": "two", "value": "two-value"}]}, '
        b'"vector": {"@class": "ai.Float32Vector", "array": [1.0, 2.0, 3.0]}, "text": "test"}'
    )
    o = serializer.deserialize(ser)
    assert isinstance(o, DocumentChunk)


# noinspection PyUnresolvedReferences
def test_SimilaritySearch_serialization() -> None:
    serializer: JSONSerializer = JSONSerializer()
    coh_fv = FloatVector([1.0, 2.0, 3.0])
    ve = Extractors.extract("foo")
    f = Filters.equals("foo", "bar")
    ss = SimilaritySearch(ve, coh_fv, 19, filter=f)
    ser = serializer.serialize(ss)
    assert ser == (
        b'\x15{"@class": "ai.search.SimilarityAggregator", '
        b'"extractor": {"@class": "extractor.UniversalExtractor", "name": "foo", "params": null}, '
        b'"algorithm": {"@class": "ai.distance.CosineSimilarity"}, '
        b'"bruteForce": false, '
        b'"filter": {"@class": "filter.EqualsFilter", '
        b'"extractor": {"@class": "extractor.UniversalExtractor", '
        b'"name": "foo", "params": null}, "value": "bar"}, "maxResults": 19, '
        b'"vector": {"@class": "ai.Float32Vector", "array": [1.0, 2.0, 3.0]}}'
    )

    o = serializer.deserialize(ser)
    assert isinstance(o, SimilaritySearch)
    assert isinstance(o.extractor, ValueExtractor)
    assert isinstance(o.algorithm, CosineDistance)
    assert isinstance(o.filter, Filter)
    assert o.maxResults == 19
    assert isinstance(o.vector, FloatVector)

    ss.bruteForce = True
    ser = serializer.serialize(ss)
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


# noinspection PyUnresolvedReferences
def test_QueryResult_serialization() -> None:
    serializer: JSONSerializer = JSONSerializer()
    bqr = QueryResult(3.0, 1, "abc")
    ser = serializer.serialize(bqr)
    assert ser == b'\x15{"@class": "ai.results.QueryResult", "distance": 3.0, "key": 1, "value": "abc"}'

    o = serializer.deserialize(ser)
    assert isinstance(o, QueryResult)
    assert o.distance == 3.0
    assert o.key == 1
    assert o.value == "abc"


# noinspection PyUnresolvedReferences
def test_BinaryQuantIndex_serialization() -> None:
    serializer: JSONSerializer = JSONSerializer()
    bqi = BinaryQuantIndex(Extractors.extract("foo"))
    ser = serializer.serialize(bqi)
    assert ser == (
        b'\x15{"@class": "ai.index.BinaryQuantIndex", "dataVersion": 0, '
        b'"binFuture": null, "extractor": {"@class": "extractor.UniversalExtractor", '
        b'"name": "foo", "params": null}, "oversamplingFactor": 3}'
    )

    o = serializer.deserialize(ser)
    assert isinstance(o, BinaryQuantIndex)
