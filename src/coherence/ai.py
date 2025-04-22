# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

import base64
from abc import ABC
from collections import OrderedDict
from typing import Any, Dict, Final, List, Optional, TypeVar, Union, cast

import jsonpickle
import numpy as np

from coherence.aggregator import EntryAggregator
from coherence.extractor import ValueExtractor
from coherence.filter import Filter
from coherence.serialization import _META_CLASS, JavaProxyUnpickler, proxy

E = TypeVar("E")
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


class Vector(ABC):
    """
    Base class that represents a Vector.

    **NOTE:** This requires using Coherence CE 24.09.2+ on the server side.
    """

    def __init__(self) -> None:
        """
        Constructs a new `Vector`.
        """
        super().__init__()


@proxy("ai.BitVector")
class BitVector(Vector):
    """
    Class that represents a Vector of Bits.

    **NOTE:** This requires using Coherence CE 24.09.2+ on the server side.
    """

    def __init__(
        self,
        hex_string: str,
        byte_array: Optional[bytes] = None,
        int_array: Optional[List[int]] = None,
    ):
        """
        Creates an instance of BitVector.

        :param hex_string: hexadecimal string used to create the BitVector.
        :param byte_array: optional byte array used to create the BitVector.
        :param int_array: optional int array used to create the BitVector.
        """
        super().__init__()
        if hex_string is not None:
            if hex_string.startswith("0x"):
                self.bits = hex_string[2:]
            else:
                self.bits = hex_string
        elif byte_array is not None:
            self.bits = byte_array.hex()
        else:
            self.bits = ""
            for i in int_array:
                self.bits += hex(i)[2:]
        self.bits = "0x" + self.bits


@proxy("ai.Int8Vector")
class ByteVector(Vector):
    """
    Class that represents Vector of bytes.

    **NOTE:** This requires using Coherence CE 24.09.2+ on the server side.
    """

    def __init__(self, byte_array: bytes):
        """
        Creates an instance of ByteVector.

        :param byte_array: byte array used to create a ByteVector.
        """
        super().__init__()
        self.array = base64.b64encode(byte_array).decode("UTF-8")


@proxy("ai.Float32Vector")
class FloatVector(Vector):
    """
    Class that represents Vector of floats.

    **NOTE:** This requires using Coherence CE 24.09.2+ on the server side.
    """

    def __init__(self, float_array: List[float]):
        """
        Creates an instance of FloatVector.

        :param float_array: array of floats used to create a FloatVector.
        """
        super().__init__()
        self.array = float_array


class AbstractEvolvable(ABC):
    def __init__(self, data_version: int = 0, bin_future: Optional[Any] = None):
        self.dataVersion = data_version
        self.binFuture = bin_future


@proxy("ai.DocumentChunk")
class DocumentChunk(AbstractEvolvable):
    """
    Class that represents a chunk of text extracted from a document.

    **NOTE:** This requires using Coherence CE 24.09.2+ on the server side.
    """

    def __init__(
        self,
        text: str,
        metadata: Optional[Union[Dict[str, Any], OrderedDict[str, Any]]] = None,
        vector: Optional[Vector] = None,
    ):
        """
        Creates an instance of DocumentChunk class.

        :param text: the chunk of text extracted from a document.
        :param metadata: optional document metadata.
        :param vector: the vector associated with the document chunk.
        """
        super().__init__()
        self.text = text
        if metadata is None:
            self.metadata: Dict[str, Any] = OrderedDict()
        else:
            self.metadata = metadata
        self.vector = vector


@jsonpickle.handlers.register(DocumentChunk)
class DocumentChunkHandler(jsonpickle.handlers.BaseHandler):
    def flatten(self, obj: object, data: Dict[str, Any]) -> Dict[str, Any]:
        dc: DocumentChunk = cast(DocumentChunk, obj)
        result_dict: Dict[Any, Any] = dict()
        result_dict[_META_CLASS] = "ai.DocumentChunk"
        result_dict["dataVersion"] = dc.dataVersion
        if hasattr(dc, "binFuture") and dc.binFuture is not None:
            result_dict["binFuture"] = dc.binFuture
        if hasattr(dc, "metadata") and dc.metadata is not None:
            result_dict["metadata"] = dict()
            if isinstance(dc.metadata, OrderedDict):
                result_dict["metadata"]["@ordered"] = True
            entries = list()
            for k, v in dc.metadata.items():
                entries.append({"key": k, "value": v})
            result_dict["metadata"]["entries"] = entries
        if hasattr(dc, "vector"):
            v = dc.vector
            if v is not None:
                if isinstance(v, BitVector):
                    result_dict["vector"] = dict()
                    result_dict["vector"][_META_CLASS] = "ai.BitVector"
                    # noinspection PyUnresolvedReferences
                    result_dict["vector"]["bits"] = v.bits
                elif isinstance(v, ByteVector):
                    result_dict["vector"] = dict()
                    result_dict["vector"][_META_CLASS] = "ai.Int8Vector"
                    # noinspection PyUnresolvedReferences
                    result_dict["vector"]["array"] = v.array
                elif isinstance(v, FloatVector):
                    result_dict["vector"] = dict()
                    result_dict["vector"][_META_CLASS] = "ai.Float32Vector"
                    # noinspection PyUnresolvedReferences
                    result_dict["vector"]["array"] = v.array
        result_dict["text"] = dc.text
        return result_dict

    def restore(self, obj: Dict[str, Any]) -> DocumentChunk:
        jpu = JavaProxyUnpickler()
        d = DocumentChunk("")
        o = jpu._restore_from_dict(obj, d)
        return o


class DistanceAlgorithm(ABC):
    """
    Base class that represents algorithm that can calculate distance to a given vector.

    **NOTE:** This requires using Coherence CE 24.09.2+ on the server side.
    """

    def __init__(self) -> None:
        super().__init__()


@proxy("ai.distance.CosineSimilarity")
class CosineDistance(DistanceAlgorithm):
    """
    Represents a DistanceAlgorithm that performs a cosine similarity calculation
    between two vectors. Cosine similarity measures the similarity between two
    vectors of an inner product space. It is measured by the cosine of the angle
    between two vectors and determines whether two vectors are pointing in
    roughly the same direction. It is often used to measure document similarity
    in text analysis.

    **NOTE:** This requires using Coherence CE 24.09.2+ on the server side.
    """

    def __init__(self) -> None:
        super().__init__()


@proxy("ai.distance.InnerProductSimilarity")
class InnerProductDistance(DistanceAlgorithm):
    """
    Represents a DistanceAlgorithm that performs inner product distance
    calculation between two vectors.

    **NOTE:** This requires using Coherence CE 24.09.2+ on the server side.
    """

    def __init__(self) -> None:
        super().__init__()


@proxy("ai.distance.L2SquaredDistance")
class L2SquaredDistance(DistanceAlgorithm):
    """
    Represents a DistanceAlgorithm that performs an L2 squared distance
    calculation between two vectors.

    **NOTE:** This requires using Coherence CE 24.09.2+ on the server side.
    """

    def __init__(self) -> None:
        super().__init__()


@proxy("ai.search.SimilarityAggregator")
class SimilaritySearch(EntryAggregator):
    """
    This class represents an aggregator to execute a similarity query.

    **NOTE:** This requires using Coherence CE 24.09.2+ on the server side.
    """

    def __init__(
        self,
        extractor_or_property: Union[ValueExtractor[T, E], str],
        vector: Vector,
        max_results: int,
        algorithm: Optional[DistanceAlgorithm] = CosineDistance(),
        filter: Optional[Filter] = None,
        brute_force: Optional[bool] = False,
    ) -> None:
        """
        Create a SimilaritySearch aggregator that will use cosine distance to
        calculate and return up to `max_results` results that are closest to the
        specified `vector`.

        :param extractor_or_property: the ValueExtractor to extract the vector
         from the cache value.
        :param vector: the vector to calculate similarity with.
        :param max_results: the maximum number of results to return.
        :param algorithm: the distance algorithm to use.
        :param filter: filter to use to limit the set of entries to search.
        :param brute_force: Force brute force search, ignoring any available indexes.
        """
        super().__init__(extractor_or_property)
        self.algorithm = algorithm
        self.bruteForce = brute_force
        self.filter = filter
        self.maxResults = max_results
        self.vector = vector


class BaseQueryResult(ABC):
    """
    A base class for QueryResult implementation.

    **NOTE:** This requires using Coherence CE 24.09.2+ on the server side.
    """

    def __init__(self, result: float, key: K, value: V) -> None:
        self.distance = result
        self.key = key
        self.value = value


@proxy("ai.results.QueryResult")
class QueryResult(BaseQueryResult):
    """
    QueryResult class.

    **NOTE:** This requires using Coherence CE 24.09.2+ on the server side.
    """

    def __init__(self, result: float, key: K, value: V) -> None:
        """
        Creates an instance of the QueryResult class.

        :param result: the query result.
        :param key: the key of the vector the result applies to.
        :param value:  the optional result value.
        """
        super().__init__(result, key, value)

    def __str__(self) -> str:
        return "QueryResult{ " + "result=" + str(self.distance) + ", key=" + str(self.key) + "}"


@proxy("ai.index.BinaryQuantIndex")
class BinaryQuantIndex(AbstractEvolvable):
    """
    This class represents a custom index using binary quantization of vectors.

    **NOTE:** This requires using Coherence CE 24.09.2+ on the server side.
    """

    def __init__(self, extractor: Union[ValueExtractor[T, E], str], over_sampling_factor: int = 3) -> None:
        """
        Creates an instance of BinaryQuantIndex class.

        :param extractor: the ValueExtractor to use to extract the Vector.
        :param over_sampling_factor: the oversampling factor.
        """
        super().__init__()
        self.extractor = extractor
        self.oversamplingFactor = over_sampling_factor


@proxy("coherence.hnsw.HnswIndex")
class HnswIndex(AbstractEvolvable):
    DEFAULT_SPACE_NAME: Final[str] = "COSINE"
    """The default index space name."""

    DEFAULT_MAX_ELEMENTS: Final[int] = 4096
    """
    The default maximum number of elements the index can contain is 4096
    but the index will grow automatically by doubling its capacity until it
    reaches approximately 8m elements, at which point it will grow by 50%
    whenever it gets full.
    """

    DEFAULT_M: Final[int] = 16
    """
    The default number of bidirectional links created for every new
    element during construction is 2-100. Higher M work better on datasets
    with high intrinsic dimensionality and/or high recall, while low M work
    better for datasets with low intrinsic dimensionality and/or low recalls.
    The parameter also determines the algorithm's memory consumption,
    which is roughly M * 8-10 bytes per stored element. As an example for
    dim=4 random vectors optimal M for search is somewhere around 6,
    while for high dimensional datasets (word embeddings, good face
    descriptors), higher M are required (e.g. M=48-64) for optimal
    performance at high recall. The range M=12-48 is ok for the most of the
    use cases. When M is changed one has to update the other parameters.
    Nonetheless, ef and ef_construction parameters can be roughly estimated
    by assuming that M*ef_{construction} is a constant. The default value is
    16.
    """

    DEFAULT_EF_CONSTRUCTION: Final[int] = 200
    """
    The parameter has the same meaning as ef, which controls the
    index_time/index_accuracy. Bigger ef_construction leads to longer
    construction, but better index quality. At some point, increasing
    ef_construction does not improve the quality of the index. One way to
    check if the selection of ef_construction was ok is to measure a recall
    for M nearest neighbor search when ef =ef_construction: if the recall is
    lower than 0.9, than there is room for improvement. The default value is
    200.
    """

    DEFAULT_EF_SEARCH: Final[int] = 50
    """
    The parameter controlling query time/accuracy trade-off. The default
    value is 50.
    """

    DEFAULT_RANDOM_SEED: Final[int] = 100
    """The default random seed used for the index."""

    def __init__(
        self,
        extractor: Union[ValueExtractor[T, E], str],
        dimension: int,
        space_name: str = DEFAULT_SPACE_NAME,
        max_elements: int = DEFAULT_MAX_ELEMENTS,
        m: int = DEFAULT_M,
        ef_construction: int = DEFAULT_EF_CONSTRUCTION,
        ef_search: int = DEFAULT_EF_SEARCH,
        random_seed: int = DEFAULT_RANDOM_SEED,
    ) -> None:
        """
        Creates an instance of HnswIndex class.

        :param extractor: The ValueExtractor to use to extract the Vector.
        :param dimension: The number of dimensions in the vector.
        :param space_name: The index space name.
        :param max_elements: The maximum number of elements the index can contain.
        :param m: The number of bidirectional links created for every new element during construction.
        :param ef_construction: The parameter controlling the index_time/index_accuracy.
        :param ef_search: The parameter controlling query time/accuracy trade-off.
        :param random_seed: The random seed used for the index.
        """

        super().__init__()
        self.extractor = extractor
        self.dimension = dimension
        self.spaceName = space_name if space_name else ""
        self.maxElements = max_elements
        self.m = m
        self.efConstruction = ef_construction
        self.efSearch = ef_search
        self.randomSeed = random_seed


class Vectors:

    EPSILON = 1e-30  # Python automatically handles float precision

    @staticmethod
    def normalize(array: list[float]) -> list[float]:
        np_array = np.array(array, dtype=np.float64)
        norm = np.linalg.norm(np_array) + Vectors.EPSILON
        normalized_array = np_array / norm
        return normalized_array.tolist()
