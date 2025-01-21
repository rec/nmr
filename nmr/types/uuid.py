from __future__ import annotations

from typing import Any
from uuid import UUID

from ..categories import Computer
from ..type_namer import TypeNamer


class Uuid(TypeNamer[UUID]):
    category = Computer.UUID

    @staticmethod
    def str_to_type(s: str) -> UUID:
        return UUID(s)

    @staticmethod
    def index_to_type(i: int) -> Any:
        return UUID(int=i)

    @staticmethod
    def type_to_index(u: UUID) -> int:
        return u.int
