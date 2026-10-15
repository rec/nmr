import fractions
import math

import pytest

from nmr.types.floating import Float
from nmr.types.fraction import Frac
from nmr.types.integer import Int


@pytest.mark.parametrize("value", ["0/0", "1/2", "2/4", "0/3", "-1/-2", "1/0", "-1/0"])
def test_fraction_pairs_preserve_identity(value: str) -> None:
    assert Frac.index_to_str(Frac.str_to_index(value)) == value


def test_fraction_conversions_delegate_without_changing_identity() -> None:
    value = Frac(numerator=2, denominator=4)
    assert value.fraction() == fractions.Fraction(1, 2)
    assert value.float() == 0.5
    assert value != Frac(numerator=1, denominator=2)
    assert value.numerator == 2 and value.denominator == 4
    assert math.isnan(Frac(numerator=0, denominator=0).float())
    assert Frac(numerator=1, denominator=0).float() == math.inf
    assert Frac(numerator=-1, denominator=0).float() == -math.inf
    with pytest.raises(ZeroDivisionError):
        Frac(numerator=0, denominator=0).fraction()
    with pytest.raises(TypeError):
        float(value)


@pytest.mark.parametrize(
    "value",
    [
        "0.0",
        "-0.0",
        "1.5",
        "inf",
        "-inf",
        "bits:7ff8000000000042",
        "bits:fff8000000000001",
    ],
)
def test_float_preserves_all_bits(value: str) -> None:
    index = Float.str_to_index(value)
    assert Float.str_to_index(Float.index_to_str(index)) == index


def test_signed_integers() -> None:
    for i in range(-100, 100):
        assert Int.index_to_str(Int.str_to_index(str(i))) == str(i)
