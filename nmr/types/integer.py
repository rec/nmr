from __future__ import annotations

from typing import Any

from ..categories import Math
from ..type_namer import TypeNamer


class Integer(TypeNamer[int]):
    category = Math.INTEGER

    @staticmethod
    def index_to_type(i: int) -> int:
        n, sign = divmod(i, 2)
        return 1 + n if sign else -n

    @staticmethod
    def type_to_index(n: int) -> int:
        return -2 * n if n <= 0 else 2 * n - 1
