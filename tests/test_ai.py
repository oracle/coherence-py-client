# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.
import random
from typing import List, Optional, cast

import pytest

from coherence import Extractors, Filters, NamedCache, Session
from coherence.ai import (
    BinaryQuantIndex,
    BitVector,
    ByteVector,
    CosineDistance,
    DocumentChunk,
    FloatVector,
    QueryResult,
    SimilaritySearch,
    Vectors,
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
def test_QueryResult_serialization() -> None:
    bqr = QueryResult(3.0, 1, "abc")
    ser = s.serialize(bqr)
    assert ser == b'\x15{"@class": "ai.results.QueryResult", "distance": 3.0, "key": 1, "value": "abc"}'

    o = s.deserialize(ser)
    assert isinstance(o, QueryResult)
    assert o.distance == 3.0
    assert o.key == 1
    assert o.value == "abc"


# noinspection PyUnresolvedReferences
def test_BinaryQuantIndex_serialization() -> None:
    bqi = BinaryQuantIndex(Extractors.extract("foo"))
    ser = s.serialize(bqi)
    assert ser == (
        b'\x15{"@class": "ai.index.BinaryQuantIndex", "dataVersion": 0, '
        b'"binFuture": null, "extractor": {"@class": "extractor.UniversalExtractor", '
        b'"name": "foo", "params": null}, "oversamplingFactor": 3}'
    )

    o = s.deserialize(ser)
    assert isinstance(o, BinaryQuantIndex)


class ValueWithVector:
    def __init__(self, vector: FloatVector, text: str, number: int) -> None:
        self.vector = vector
        self.text = text
        self.number = number

    def get_vector(self) -> FloatVector:
        return self.vector

    def get_text(self) -> str:
        return self.text

    def get_number(self) -> int:
        return self.number

    def __repr__(self) -> str:
        return f"ValueWithVector(vector={self.vector}, text='{self.text}', number={self.number})"


def random_floats(n: int) -> List[float]:
    floats: List[float] = [0.0] * n
    for i in range(n):
        floats[i] = random.uniform(-50.0, 50.0)
    return floats


DIMENSIONS: int = 384


async def populate_vectors(vectors: NamedCache[int, ValueWithVector]) -> ValueWithVector:
    matches: List[List[float]] = [[]] * 5
    matches[0] = random_floats(DIMENSIONS)

    # Creating copies of matches[0] for matches[1] to matches[4]
    for i in range(1, 5):
        matches[i] = matches[0].copy()
        matches[i][0] += 1.0  # Modify the first element

    values: List[Optional[ValueWithVector]] = [None] * 10000

    # Assign normalized vectors to the first 5 entries
    for i in range(5):
        values[i] = ValueWithVector(FloatVector(Vectors.normalize(matches[i])), str(i), i)
        await vectors.put(i, values[i])

    # Fill the remaining values with random vectors
    for i in range(5, 10000):
        values[i] = ValueWithVector(FloatVector(Vectors.normalize(random_floats(DIMENSIONS))), str(i), i)
        await vectors.put(i, values[i])

    return cast(ValueWithVector, values[0])


@pytest.mark.asyncio
async def test_SimilaritySearch() -> None:
    session: Session = await Session.create()
    cache: NamedCache[int, ValueWithVector] = await session.get_cache("vector_cache")
    value_with_vector = await populate_vectors(cache)

    # Create a SimilaritySearch aggregator
    value_extractor = Extractors.extract("vector")
    k = 10
    ss = SimilaritySearch(value_extractor, value_with_vector.vector, 10)

    hnsw_result = await cache.aggregate(ss)

    assert hnsw_result is not None
    assert len(hnsw_result) == k

    await cache.truncate()
    await cache.destroy()
    await session.close()


async def populate_documentchunk_vectors(vectors: NamedCache[int, DocumentChunk]) -> DocumentChunk:
    matches: List[List[float]] = [[]] * 5
    matches[0] = random_floats(DIMENSIONS)

    # Creating copies of matches[0] for matches[1] to matches[4]
    for i in range(1, 5):
        matches[i] = matches[0].copy()
        matches[i][0] += 1.0  # Modify the first element

    values: List[Optional[DocumentChunk]] = [None] * 10000

    # Assign normalized vectors to the first 5 entries
    for i in range(5):
        values[i] = DocumentChunk(str(i), metadata=None, vector=FloatVector(Vectors.normalize(matches[i])))
        await vectors.put(i, values[i])

    # Fill the remaining values with random vectors
    for i in range(5, 10000):
        values[i] = DocumentChunk(
            str(i), metadata=None, vector=FloatVector(Vectors.normalize(random_floats(DIMENSIONS)))
        )
        await vectors.put(i, values[i])

    return cast(DocumentChunk, values[0])


@pytest.mark.asyncio
async def test_SimilaritySearch_with_DocumentChunk() -> None:
    session: Session = await Session.create()
    cache: NamedCache[int, DocumentChunk] = await session.get_cache("vector_cache")
    dc: DocumentChunk = await populate_documentchunk_vectors(cache)

    # Create a SimilaritySearch aggregator
    value_extractor = Extractors.extract("vector")
    k = 10
    ss = SimilaritySearch(value_extractor, dc.vector, 10)

    hnsw_result = await cache.aggregate(ss)

    assert hnsw_result is not None
    assert len(hnsw_result) == k

    await cache.truncate()
    await cache.destroy()
    await session.close()
