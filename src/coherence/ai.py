# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

import base64
from abc import ABC
from collections import OrderedDict
from typing import Any, Dict, List, Optional, TypeVar, Union, cast
import numpy as np

import jsonpickle

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


class Vectors:

    EPSILON = 1e-30  # Python automatically handles float precision

    @staticmethod
    def normalize_numpy(array: list[float]) -> list[float]:
        np_array = np.array(array, dtype=np.float64)
        norm = np.linalg.norm(np_array) + Vectors.EPSILON
        normalized_array = np_array / norm
        return normalized_array.tolist()