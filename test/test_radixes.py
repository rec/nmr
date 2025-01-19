import pytest

from nmr.radixes import Radixes

RADIXES = Radixes(2, 2, 23, 19, 2)
NUMBERS = 0, 1, 2, 100, 1028, 1001239212


@pytest.mark.parametrize("number", NUMBERS)
def test_radixes(number):
    parts = RADIXES.decode(number)
    number2 = RADIXES.encode(*parts)
    assert number == number2
