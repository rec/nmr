from uuid import UUID

from ..type_truenamer import TypeTruenamer
from .bounded import bounded


class Uuid(TypeTruenamer):
    label = "uuid"
    description = "UUID preserving all 128 bits"

    @staticmethod
    def str_to_index(value: str) -> int:
        return UUID(value).int

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        return str(UUID(int=bounded(index, 2**128, browse)))
