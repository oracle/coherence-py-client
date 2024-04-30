# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

from abc import ABC
from typing import Any

from .extractor import UniversalExtractor
from .serialization import proxy


class Comparator(ABC):
    """Comparator is used to control the ordering for collections of objects"""

    def __init__(self) -> None:
        super().__init__()


@proxy("comparator.SafeComparator")
class SafeComparator(Comparator):
    """None-safe delegating comparator. None values are evaluated as "less then" any non None value."""

    def __init__(self, property_name: str) -> None:
        super().__init__()
        self.comparator = ExtractorComparator(property_name)


@proxy("comparator.InverseComparator")
class InverseComparator(Comparator):
    """Comparator that reverses the result of another comparator."""

    def __init__(self, property_name: str) -> None:
        super().__init__()
        self.comparator = ExtractorComparator(property_name)


@proxy("comparator.ExtractorComparator")
class ExtractorComparator(Comparator):
    """Comparator implementation that uses specified :class:`coherence.extractor.ValueExtractor` to
    extract value(s) to be used for comparison."""

    def __init__(self, property_name: str) -> None:
        super().__init__()
        self.extractor = UniversalExtractor[Any](property_name)
