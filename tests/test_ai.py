# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.
import random
import time
from typing import List, Optional, cast

import pytest

from coherence import COH_LOG, Extractors, NamedCache, Session
from coherence.ai import BinaryQuantIndex, DocumentChunk, FloatVector, SimilaritySearch, Vectors


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

    count = 10000
    values: List[Optional[ValueWithVector]] = [None] * count

    # Assign normalized vectors to the first 5 entries
    for i in range(5):
        values[i] = ValueWithVector(FloatVector(Vectors.normalize(matches[i])), str(i), i)
        await vectors.put(i, values[i])

    # Fill the remaining values with random vectors
    for i in range(5, count):
        values[i] = ValueWithVector(FloatVector(Vectors.normalize(random_floats(DIMENSIONS))), str(i), i)
        await vectors.put(i, values[i])

    return cast(ValueWithVector, values[0])


@pytest.mark.asyncio
async def test_SimilaritySearch_with_Index() -> None:
    session: Session = await Session.create()
    cache: NamedCache[int, ValueWithVector] = await session.get_cache("vector_cache")
    cache.add_index(BinaryQuantIndex(Extractors.extract("vector")))
    value_with_vector = await populate_vectors(cache)

    # Create a SimilaritySearch aggregator
    value_extractor = Extractors.extract("vector")
    k = 10
    ss = SimilaritySearch(value_extractor, value_with_vector.vector, k)

    ss.bruteForce = True  # Set bruteForce to True
    start_time_bf = time.perf_counter()
    hnsw_result = await cache.aggregate(ss)
    end_time_bf = time.perf_counter()
    elapsed_time = end_time_bf - start_time_bf
    COH_LOG.info("Results below for test_SimilaritySearch with BruteForce true:")
    for e in hnsw_result:
        COH_LOG.info(e)
    COH_LOG.info(f"Elapsed time for brute force: {elapsed_time} seconds")

    assert hnsw_result is not None
    assert len(hnsw_result) == k

    ss.bruteForce = False
    start_time = time.perf_counter()
    hnsw_result = await cache.aggregate(ss)
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    COH_LOG.info("Results below for test_SimilaritySearch with Index:")
    for e in hnsw_result:
        COH_LOG.info(e)
    COH_LOG.info(f"Elapsed time: {elapsed_time} seconds")

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

    count = 10000
    values: List[Optional[DocumentChunk]] = [None] * count

    # Assign normalized vectors to the first 5 entries
    for i in range(5):
        values[i] = DocumentChunk(str(i), metadata=None, vector=FloatVector(Vectors.normalize(matches[i])))
        await vectors.put(i, values[i])

    # Fill the remaining values with random vectors
    for i in range(5, count):
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
    ss = SimilaritySearch(value_extractor, dc.vector, k)

    hnsw_result = await cache.aggregate(ss)

    assert hnsw_result is not None
    assert len(hnsw_result) == k
    COH_LOG.info("Results below for test_SimilaritySearch_with_DocumentChunk:")
    for e in hnsw_result:
        COH_LOG.info(e)

    await cache.truncate()
    await cache.destroy()
    await session.close()
