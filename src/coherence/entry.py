# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class MapEntry(Generic[K, V]):
    """
    A map entry (key-value pair).
    """

    def __init__(self, key: K, value: V):
        self._key = key
        self._value = value

    @property
    def key(self) -> K:
        return self._key

    @property
    def value(self) -> V:
        return self._value

    def __str__(self) -> str:
        return f"MapEntry(key={self.key}, value={self.value})"
