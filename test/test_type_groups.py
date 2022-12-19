from nmr.types import type_groups as tg
import pytest

ROUND_TRIP_CASES = [
    (0, 0, tg.Math.INTEGER),
    (1, 0, tg.Science.ELEMENT),
    (2, 0, tg.Music.RHYTHM),
    (7, 0, tg.Commercial.ISBN),

]

NON_ROUND_TRIP_CASES = [
    (8, 0, tg.Math.INTEGER),
]

ALL_CASES = (
    list(range(16))
    + list(range(n := 109223, n + 32))
    + list(range(n := 3458702354876246, n + 32))
)


def test_simple():
    assert tg.number_to_remainder_and_type(8) == (0, tg.Math.INTEGER)


@pytest.mark.parametrize('n,d,t', ROUND_TRIP_CASES)
def test_type_groups(n, d, t):
    assert t.type_to_number(d) == n
    assert tg.number_to_remainder_and_type(n) == (d, t)


@pytest.mark.parametrize('n,d,t', NON_ROUND_TRIP_CASES)
def test_type_groups_non(n, d, t):
    assert (n2 := t.type_to_number(d)) != n
    assert t.type_to_number(n2) == n2
    assert tg.number_to_remainder_and_type(n) == (d, t)


@pytest.mark.parametrize('n', ALL_CASES)
def test_type_groups_all(n):
    r, t = tg.number_to_remainder_and_type(n)
    n2 = t.type_to_number(r)

    assert tg.number_to_remainder_and_type(n2) == (r, t)
