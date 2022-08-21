from . base import Base
from typing import Optional
import uuid


class Uuid(Base):
    type = uuid.UUID

    @staticmethod
    def to_int(s: str) -> Optional[int]:
        if len(s) == 36 and s.count('-') == 4:
            return uuid.UUID(s).int

    @staticmethod
    def int_to_type(i: int) -> Optional[str]:
        return uuid.UUID(int=i)
