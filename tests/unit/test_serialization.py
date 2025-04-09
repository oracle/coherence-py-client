# Copyright (c) 2022, 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from decimal import Decimal
from time import time
from typing import Any
from uuid import uuid4

from coherence import Extractors, Filters
from coherence.ai import (
    BinaryQuantIndex,
    BitVector,
    ByteVector,
    CosineDistance,
    DocumentChunk,
    FloatVector,
    HnswIndex,
    QueryResult,
    SimilaritySearch,
)
from coherence.extractor import ValueExtractor
from coherence.filter import Filter
from coherence.serialization import JSONSerializer, SerializerRegistry, mappings, proxy

s = SerializerRegistry.serializer(JSONSerializer.SER_FORMAT)


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


@proxy("Task")
@mappings({"created_at": "createdAt"})
class Task:
    def __init__(self, description: str) -> None:
        super().__init__()
        self.id: str = str(uuid4())[0:6]
        self.description: str = description
        self.completed: bool = False
        self.created_at: int = int(time() * 1000)

    def __hash__(self) -> int:
        return hash((self.id, self.description, self.completed, self.created_at))

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Task):
            # noinspection PyTypeChecker
            t: Task = o
            return (
                self.id == t.id
                and self.description == t.description
                and self.completed == t.completed
                and self.created_at == t.created_at
            )
        return False

    def __str__(self) -> str:
        return 'Task(id="{}", description="{}", completed={}, created_at={})'.format(
            self.id, self.description, self.completed, self.created_at
        )


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


def test_bit_vector_serialization() -> None:
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


def test_byte_vector_serialization() -> None:
    coh_int8v = ByteVector(bytes([1, 2, 3, 4]))
    ser = s.serialize(coh_int8v)
    assert ser == b'\x15{"@class": "ai.Int8Vector", "array": "AQIDBA=="}'
    o = s.deserialize(ser)
    assert isinstance(o, ByteVector)


def test_float_vector_serialization() -> None:
    coh_fv = FloatVector([1.0, 2.0, 3.0])
    ser = s.serialize(coh_fv)
    assert ser == b'\x15{"@class": "ai.Float32Vector", "array": [1.0, 2.0, 3.0]}'
    o = s.deserialize(ser)
    assert isinstance(o, FloatVector)


def test_document_chunk_serialization() -> None:
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
def test_similarity_search_serialization() -> None:
    coh_fv = FloatVector([1.0, 2.0, 3.0])
    ve = Extractors.extract("foo")
    f = Filters.equals("foo", "bar")
    ss = SimilaritySearch(ve, coh_fv, 19, filter=f)
    ser = s.serialize(ss)
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

    o = s.deserialize(ser)
    assert isinstance(o, SimilaritySearch)
    assert isinstance(o.extractor, ValueExtractor)
    assert isinstance(o.algorithm, CosineDistance)
    assert isinstance(o.filter, Filter)
    assert o.maxResults == 19
    assert isinstance(o.vector, FloatVector)

    ss.bruteForce = True
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


# noinspection PyUnresolvedReferences
def test_query_result_serialization() -> None:
    bqr = QueryResult(3.0, 1, "abc")
    ser = s.serialize(bqr)
    assert ser == b'\x15{"@class": "ai.results.QueryResult", "distance": 3.0, "key": 1, "value": "abc"}'

    o = s.deserialize(ser)
    assert isinstance(o, QueryResult)
    assert o.distance == 3.0
    assert o.key == 1
    assert o.value == "abc"


# noinspection PyUnresolvedReferences
def test_binary_quant_index_serialization() -> None:
    bqi = BinaryQuantIndex(Extractors.extract("foo"))
    ser = s.serialize(bqi)
    assert ser == (
        b'\x15{"@class": "ai.index.BinaryQuantIndex", "dataVersion": 0, '
        b'"binFuture": null, "extractor": {"@class": "extractor.UniversalExtractor", '
        b'"name": "foo", "params": null}, "oversamplingFactor": 3}'
    )

    o = s.deserialize(ser)
    assert isinstance(o, BinaryQuantIndex)


# noinspection PyUnresolvedReferences
def test_HnswIndex_serialization() -> None:
    bqi = HnswIndex(Extractors.extract("foo"), 384)
    ser = s.serialize(bqi)
    assert ser == (
        b'\x15{"@class": "coherence.hnsw.HnswIndex", "dataVersion": 0, '
        b'"binFuture": null, "extractor": {"@class": "extractor.UniversalExtractor", '
        b'"name": "foo", "params": null}, "dimensions": 384, "spaceName": "COSINE", '
        b'"maxElements": 4096, "m": 16, "efConstruction": 200, "efSearch": 50, '
        b'"randomSeed": 100}'
    )

    o = s.deserialize(ser)
    assert isinstance(o, HnswIndex)
