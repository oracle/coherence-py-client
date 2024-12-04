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
