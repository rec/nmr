from __future__ import annotations

import fractions
import math
from typing import Any

from ..categories import Math
from ..nameable_type import NameableType

D: dict[str, Any] = {}


class Fraction(NameableType[fractions.Fraction]):
    category = Math.FRACTION

    """
    Use a Cantor-style diagonal argument
    numerator, denominator:

    TODO: use packed_number
    """

    @staticmethod
    def type_to_index(t: fractions.Fraction) -> int:
        num, denom = t.as_integer_ratio()
        if num >= 0:
            sign = 0
        else:
            sign = 1
            num = -num

        width = num + denom - 1
        index = width * (width - 1) // 2
        index_plus_denom = index + denom - 1

        return 2 * index_plus_denom + sign

    @staticmethod
    def index_to_type(i: int) -> fractions.Fraction:
        index_plus_denom, sign = divmod(i, 2)

        # https://math.stackexchange.com/a/1417583/127733
        # Largest triangular number less than x
        width = index_plus_denom and (
            int((1 + math.sqrt(8 * index_plus_denom + 1)) / 2)
        )
        index = width * (width - 1) // 2

        denom = index_plus_denom - index + 1
        num = width - denom + 1
        if sign:
            num = -num

        return fractions.Fraction(num, denom)
