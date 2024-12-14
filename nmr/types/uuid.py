from __future__ import annotations

import uuid
from typing import Any

from ..nameable_type import NameableType


class Uuid(NameableType):
    type: type = uuid.UUID

    @staticmethod
    def to_int(s: str) -> int | None:
        if len(s) == 36 and s.count("-") == 4:
            try:
                u = uuid.UUID(s)
            except Exception:
                return None
            return u.int
        return None

    @staticmethod
    def int_to_type(i: int) -> Any:
        return uuid.UUID(int=i)
