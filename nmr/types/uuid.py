import uuid
from typing import Optional

from ..type_base import Type


class Uuid(Type):
    type = uuid.UUID

    @staticmethod
    def to_int(s: str) -> Optional[int]:
        if len(s) == 36 and s.count("-") == 4:
            try:
                u = uuid.UUID(s)
            except Exception:
                return
            return u.int

    @staticmethod
    def int_to_type(i: int) -> Optional[str]:
        return uuid.UUID(int=i)
