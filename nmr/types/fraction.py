import fractions
import math
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from ..pack_numbers import pair, unpair
from ..type_name import TypeNamer
from .integer import parse_integer, signed_index, signed_value


class Frac(BaseModel, TypeNamer, frozen=True):
    numerator: int
    denominator: int
    label: ClassVar[str] = "frac"
    description: ClassVar[str] = "Exact numerator/denominator pair, including 0/0"

    def float(self) -> float:
        if self.denominator == 0:
            if self.numerator == 0:
                return math.nan
            return math.inf if self.numerator > 0 else -math.inf
        return float(self.fraction())

    def fraction(self) -> fractions.Fraction:
        return fractions.Fraction(self.numerator, self.denominator)

    @staticmethod
    def str_to_index(value: str) -> int:
        parts = value.split("/")
        if len(parts) != 2:
            raise ValueError("Expected numerator/denominator")
        return pair(*(signed_index(parse_integer(i)) for i in parts))

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        numerator, denominator = (signed_value(i) for i in unpair(index))
        return f"{numerator}/{denominator}"

    model_config = ConfigDict(strict=True)
