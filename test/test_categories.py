from __future__ import annotations

import pytest

from nmr import categories

ROUND_TRIP_CASES = [
    (0, 0, categories.Math.INTEGER),
    (1, 0, categories.Science.ELEMENT),
    (2, 0, categories.Music.RHYTHM),
    (7, 0, categories.Commercial.ISBN),
]

NON_ROUND_TRIP_CASES = [
    (8, 0, categories.Math.INTEGER),
]

ALL_CASES = (
    list(range(16))
    + list(range(n := 109223, n + 32))
    + list(range(n := 3458702354876246, n + 32))
)


def test_simple():
    assert categories.number_to_remainder_and_type(8) == (0, categories.Math.INTEGER)


@pytest.mark.parametrize("n,d,t", ROUND_TRIP_CASES)
def test_categories(n, d, t):
    assert t.type_to_number(d) == n
    assert categories.number_to_remainder_and_type(n) == (d, t)


@pytest.mark.parametrize("n,d,t", NON_ROUND_TRIP_CASES)
def test_categories_non(n, d, t):
    assert (n2 := t.type_to_number(d)) != n
    assert t.type_to_number(n2) == n2
    assert categories.number_to_remainder_and_type(n) == (d, t)


@pytest.mark.parametrize("n", ALL_CASES)
def test_categories_all(n):
    r, t = categories.number_to_remainder_and_type(n)
    n2 = t.type_to_number(r)

    assert categories.number_to_remainder_and_type(n2) == (r, t)
