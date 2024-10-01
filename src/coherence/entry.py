from __future__ import annotations

from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class MapEntry(Generic[K, V]):
    """
    A map entry (key-value pair).
    """

    def __init__(self, key: K, value: V):
        self.key = key
        self.value = value
