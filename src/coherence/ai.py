# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

import base64
from abc import ABC
from collections import OrderedDict
from typing import Any, Dict, List, Optional, TypeVar, Union, cast

import jsonpickle

from coherence.aggregator import EntryAggregator
from coherence.extractor import ValueExtractor
from coherence.filter import Filter
from coherence.serialization import JavaProxyUnpickler, proxy

E = TypeVar("E")
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


class Vector(ABC):
    def __init__(self) -> None:
        """
        Constructs a new `Vector`.
        """
        super().__init__()


@proxy("ai.BitVector")
class BitVector(Vector):
    def __init__(
        self,
        hex_string: str,
        byte_array: Optional[bytes] = None,
        int_array: Optional[List[int]] = None,
    ):
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
    def __init__(self, byte_array: bytes):
        super().__init__()
        self.array = base64.b64encode(byte_array).decode("UTF-8")


@proxy("ai.Float32Vector")
class FloatVector(Vector):
    def __init__(self, float_array: List[float]):
        super().__init__()
        self.array = float_array


class AbstractEvolvable(ABC):
    def __init__(self, data_version: int = 0, bin_future: Optional[Any] = None):
        self.dataVersion = data_version
        self.binFuture = bin_future


@proxy("ai.DocumentChunk")
class DocumentChunk(AbstractEvolvable):
    def __init__(
        self,
        text: str,
        metadata: Optional[Dict[str, Any] | OrderedDict[str, Any]] = None,
        vector: Optional[Vector] = None,
    ):
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
        result_dict["@class"] = "ai.DocumentChunk"
        result_dict["dataVersion"] = dc.dataVersion
        if hasattr(dc, "binFuture"):
            if dc.binFuture is not None:
                result_dict["binFuture"] = dc.binFuture
        if hasattr(dc, "metadata"):
            if dc.metadata is not None:
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
                    result_dict["vector"]["@class"] = "ai.BitVector"
                    # noinspection PyUnresolvedReferences
                    result_dict["vector"]["bits"] = v.bits
                elif isinstance(v, ByteVector):
                    result_dict["vector"] = dict()
                    result_dict["vector"]["@class"] = "ai.Int8Vector"
                    # noinspection PyUnresolvedReferences
                    result_dict["vector"]["array"] = v.array
                elif isinstance(v, FloatVector):
                    result_dict["vector"] = dict()
                    result_dict["vector"]["@class"] = "ai.Float32Vector"
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
    def __init__(self) -> None:
        super().__init__()


@proxy("ai.distance.CosineSimilarity")
class CosineDistance(DistanceAlgorithm):
    def __init__(self) -> None:
        super().__init__()


@proxy("ai.distance.InnerProductSimilarity")
class InnerProductDistance(DistanceAlgorithm):
    def __init__(self) -> None:
        super().__init__()


@proxy("ai.distance.L2SquaredDistance")
class L2SquaredDistance(DistanceAlgorithm):
    def __init__(self) -> None:
        super().__init__()


@proxy("ai.search.SimilarityAggregator")
class SimilaritySearch(EntryAggregator):
    def __init__(
        self,
        extractor_or_property: Union[ValueExtractor[T, E], str],
        vector: Vector,
        max_results: int,
        algorithm: Optional[DistanceAlgorithm] = CosineDistance(),
        filter: Optional[Filter] = None,
        brute_force: Optional[bool] = True,
    ) -> None:
        super().__init__(extractor_or_property)
        self.algorithm = algorithm
        self.bruteForce = brute_force
        self.filter = filter
        self.maxResults = max_results
        self.vector = vector


class BaseQueryResult(ABC):
    def __init__(self, result: float, key: K, value: V) -> None:
        self.distance = result
        self.key = key
        self.value = value


@proxy("ai.results.BinaryQueryResult")
class BinaryQueryResult(BaseQueryResult):
    def __init__(self, result: float, key: K, value: V) -> None:
        super().__init__(result, key, value)
