from __future__ import annotations

from typing import Any, Type


class NameableType:
    type: type = str

    @classmethod
    def from_int(cls, i: int, name: str = "str") -> str:
        c = str(cls.int_to_type(i))
        if c is not None:
            return c

        raise ValueError(f'Can\'t convert "{i}" ({name}) to {cls.__name__}')

    @classmethod
    def int_to_type(cls, i: int) -> Any:
        return cls.type(i)

    @classmethod
    def int_to_str(cls, i: int) -> Any:
        return str(cls.int_to_type(i))

    @staticmethod
    def type_to_int(t: Any) -> int | None:
        try:
            return int(t)
        except Exception:
            return None

    @classmethod
    def to_int(cls, s: str) -> int | None:
        return cls.type_to_int(cls.type(s))
