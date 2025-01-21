from __future__ import annotations

import fractions
import math
from typing import Any

from ..category import Math
from ..pack_numbers import Packer
from ..type_namer import TypeNamer

packer = Packer(2)


class Fraction(TypeNamer[fractions.Fraction]):
    category = Math.FRACTION

    @staticmethod
    def type_to_index(t: fractions.Fraction) -> int:
        if not t:
            return 0
        num, denom = t.as_integer_ratio()
        assert num and denom
        if num > 0:
            num = num * 2 - 1
        else:
            num = -num * 2
        return 1 + packer.pack(num - 1, denom - 1)

    @staticmethod
    def index_to_type(i: int) -> fractions.Fraction:
        if not i:
            return fractions.Fraction(0)

        num, denom = packer.unpack(i - 1)
        num += 1
        denom += 1
        if num % 2:
            num = (num + 1) // 2
        else:
            num = -num // 2

        return fractions.Fraction(num, denom)
