# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

import base64
from abc import ABC
from typing import Optional

from coherence.serialization import proxy


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
        int_array: Optional[list[int]] = None,
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
    def __init__(self, float_array: list[float]):
        super().__init__()
        self.array = float_array
