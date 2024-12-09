from __future__ import annotations

import uuid

from ..nameable_type import NameableType


class Uuid(NameableType):
    type = uuid.UUID

    @staticmethod
    def to_int(s: str) -> int | None:
        if len(s) == 36 and s.count("-") == 4:
            try:
                u = uuid.UUID(s)
            except Exception:
                return
            return u.int

    @staticmethod
    def int_to_type(i: int) -> str | None:
        return uuid.UUID(int=i)
