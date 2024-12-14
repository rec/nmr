from __future__ import annotations

from typing import Any

from ..nameable_type import NameableType


class Integer(NameableType):
    @staticmethod
    def type_to_int(s: str) -> Any:
        try:
            return int(s)
        except ValueError:
            return None
