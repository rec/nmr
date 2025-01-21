from __future__ import annotations

import pytest

from nmr import category

ROUND_TRIP_CASES = [
    (0, 0, category.Math.INTEGER),
    (1, 0, category.Science.ELEMENT),
    (2, 0, category.Art.MUSIC),
    (6, 0, category.Commercial.ISBN),
]

NON_ROUND_TRIP_CASES = []

ALL_CASES = (
    list(range(16))
    + list(range(n := 109223, n + 32))
    + list(range(n := 3458702354876246, n + 32))
)


def test_simple():
    assert category.make_category(8) == (category.Math.FRACTION, 0)


@pytest.mark.parametrize("n,d,t", ROUND_TRIP_CASES)
def test_category(n, d, t):
    assert t.number_to_index(d) == n
    assert category.make_category(n) == (t, d)


@pytest.mark.parametrize("n,d,t", NON_ROUND_TRIP_CASES)
def test_category_non(n, d, t):
    assert (n2 := t.number_to_index(d)) != n
    assert t.number_to_index(n2) == n2
    assert category.make_category(n) == (t, d)


@pytest.mark.parametrize("n", ALL_CASES)
def test_category_all(n):
    t, r = category.make_category(n)
    n2 = t.number_to_index(r)

    assert category.make_category(n2) == (t, r)
