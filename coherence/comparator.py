# Copyright (c) 2022 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

from abc import ABC

from coherence.extractor import UniversalExtractor
from coherence.serialization import proxy


class Comparator(ABC):
    def __init__(self) -> None:
        super().__init__()


@proxy("comparator.SafeComparator")
class SafeComparator(Comparator):
    def __init__(self, property_name: str) -> None:
        super().__init__()
        self.comparator = ExtractorComparator(property_name)


@proxy("comparator.InverseComparator")
class InverseComparator(Comparator):
    def __init__(self, property_name: str) -> None:
        super().__init__()
        self.comparator = ExtractorComparator(property_name)


@proxy("comparator.ExtractorComparator")
class ExtractorComparator(Comparator):
    def __init__(self, property_name: str) -> None:
        super().__init__()
        self.extractor = UniversalExtractor(property_name)
