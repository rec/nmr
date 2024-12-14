from __future__ import annotations

from ..nameable_type import NameableType


class Hex(NameableType):
    @staticmethod
    def type_to_int(s: str) -> int | None:
        s = s.lower()
        if s.startswith("0x"):
            return int(s[2:], 16)
        if s.startswith("-0x"):
            return -int(s[2:], 16)
        return None

    int_to_type = staticmethod(hex)  # type: ignore[assignment]
