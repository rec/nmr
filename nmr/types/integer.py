from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from ..type_namer import TypeNamer


class Int(BaseModel, TypeNamer, frozen=True):
    value: int
    label: ClassVar[str] = "int"
    description: ClassVar[str] = "Signed integer"

    @staticmethod
    def str_to_index(value: str) -> int:
        return signed_index(int(value))

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        return str(signed_value(index))

    model_config = ConfigDict(strict=True)


def signed_index(n: int) -> int:
    return 2 * n - 1 if n > 0 else -2 * n


def signed_value(n: int) -> int:
    if n < 0:
        raise ValueError("Expected a nonnegative index")
    return (n + 1) // 2 if n % 2 else -n // 2
