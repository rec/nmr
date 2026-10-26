import re
from decimal import Decimal
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from ..type_truenamer import TypeTruenamer


class Int(BaseModel, TypeTruenamer, frozen=True):
    value: int
    label: ClassVar[str] = "int"
    description: ClassVar[str] = "Signed integer"

    @staticmethod
    def str_to_index(value: str) -> int:
        return signed_index(parse_integer(value))

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        return format(Decimal(signed_value(index)), "f")

    model_config = ConfigDict(strict=True)


def signed_index(n: int) -> int:
    return 2 * n - 1 if n > 0 else -2 * n


def parse_integer(value: str) -> int:
    value = value.strip()
    if not re.fullmatch(r"[+-]?[0-9]+", value):
        raise ValueError("Expected a signed decimal integer")
    return int(Decimal(value))


def signed_value(n: int) -> int:
    if n < 0:
        raise ValueError("Expected a nonnegative index")
    return (n + 1) // 2 if n % 2 else -n // 2
