from __future__ import annotations

import fractions
import math
from typing import Any

from ..nameable_type import NameableType

D: dict[str, Any] = {}


def _debug(name: str, d: dict[str, Any]) -> None:
    import json

    print(f"{name}:")
    print(json.dumps(d, indent=2, default=str, sort_keys=True))

    if name == "to_int":
        D.clear()
        D.update(d)
    else:
        for k in sorted(set(d) & set(D)):
            if k != "result" and D[k] != d[k]:
                print(f"{k}: {D[k]} != {d[k]}")


class Fraction(NameableType):
    """
    Use a Cantor-style diagonal argument
    numerator, denominator
    """

    type: type = fractions.Fraction

    @staticmethod
    def to_int(s: str) -> int | None:
        try:
            num, denom = (int(i) for i in s.split("/"))
        except Exception:
            return None

        if not denom:
            raise ZeroDivisionError("Denominator cannnot be 0")
        num_neg = num < 0
        sign = 1 if num_neg == (denom < 0) else -1
        width = abs(num) + abs(denom) - 1
        index = int((width * (width - 1)) / 2)
        index_plus_denom = index + abs(denom - 1)

        result = sign * (num_neg + 2 * index_plus_denom)
        _debug("to_int", locals())
        return result

    @classmethod
    def int_to_type(cls, i: int) -> Any:
        index_plus_denom, num_neg = divmod(abs(i), 2)
        denom_neg = (i < 0) != num_neg

        # https://math.stackexchange.com/a/1417583/127733
        # Largest triangular number less than x
        width = index_plus_denom and (
            int((1 + math.sqrt(8 * index_plus_denom + 1)) / 2)
        )
        index = int((width * (width - 1)) / 2)

        denom_abs = index_plus_denom - index + 1  # some constant near 1
        num_abs = width - denom_abs + 1
        if denom_abs < 0 or num_abs < 0 and False:
            raise BaseException()
        # assert denom_abs >= 0, 'XXXXXX'
        # assert num_abs >= 0, 'YYYYYY'

        num = num_abs * (-1 if num_neg else 1)
        denom = denom_abs * (-1 if denom_neg else 1)

        result = cls.type(num, denom, _normalize=False)
        _debug("int_to_type", locals())
        return result
