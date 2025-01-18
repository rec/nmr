import bisect
import dataclasses as dc
import math
from typing import Sequence

"""
A module for packing n numbers into a single number
"""


@dc.dataclass(frozen=True)
class Packer:
    count: int
    forward: bool = True

    def __post_init__(self) -> None:
        assert self.count >= 1

    def pack(self, sequence: Sequence[int]) -> int:
        if len(sequence) == self.count:
            return self._pack(sequence)

        raise ValueError(f"{len(sequence)=} != {self.count=}")

    def unpack(self, n: int) -> list[int]:
        return self._unpack(n, self.count)

    def _pack(self, a: Sequence[int]) -> int:
        if len(a) == 1:
            return a[0]

        if self.forward:
            x, *rest = a
            y = self._pack(rest)
        else:
            *rest, y = a
            x = self._pack(rest)

        return _cantor(x, y)

    def _unpack(self, n: int, count: int) -> list[int]:
        if count == 1:
            return [n]

        x, y = _inverse_cantor(n)
        if self.forward:
            return [x] + self._unpack(y, count - 1)
        else:
            return self._unpack(x, count - 1) + [y]


# https://en.wikipedia.org/wiki/Pairing_function#Cantor_pairing_function


def _cantor(x: int, y: int) -> int:
    return (x + y) * (x + y + 1) // 2 + y


def _inverse_cantor(z: int) -> tuple[int, int]:
    w = int((math.sqrt(8 * z + 1) - 1) / 2)
    t = (w * w + w) // 2
    y = z - t
    x = w - y
    return x, y
