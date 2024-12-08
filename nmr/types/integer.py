from __future__ import annotations

from typing import Any

from ..type_base import Type


class Integer(Type):
    @staticmethod
    def type_to_int(s: str) -> Any | None:
        try:
            return int(s)
        except ValueError:
            return
