from __future__ import annotations

from typing import Any, Type


class NameableType:
    type: type = str

    @classmethod
    def int_to_type(cls, i: int) -> Any:
        return cls.type(i)

    @staticmethod
    def type_to_int(t: Any) -> int | None:
        try:
            return int(t)
        except Exception:
            return None

    @classmethod
    def to_int(cls, s: str) -> int | None:
        return cls.type_to_int(cls.type(s))
