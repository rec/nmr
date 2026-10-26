import math
import struct
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field

from ..type_truenamer import TypeTruenamer


class Float(BaseModel, TypeTruenamer, frozen=True):
    """An IEEE 754 binary64 truename; NaN payloads remain distinct."""

    bits: int = Field(ge=0, lt=2**64)
    label: ClassVar[str] = "float"
    description: ClassVar[str] = "Binary64 float; hexadecimal bits preserve every NaN"

    def float(self) -> float:
        return struct.unpack(">d", self.bits.to_bytes(8, "big"))[0]

    @staticmethod
    def str_to_index(value: str) -> int:
        if value.startswith("bits:"):
            bits = int(value[5:], 16)
            if not 0 <= bits < 2**64:
                raise ValueError("Float bits must fit in 64 bits")
            return bits
        return int.from_bytes(struct.pack(">d", float(value)), "big")

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        if browse:
            index %= 2**64
        number = Float(bits=index).float()
        return f"bits:{index:016x}" if math.isnan(number) else repr(number)

    model_config = ConfigDict(strict=True)
