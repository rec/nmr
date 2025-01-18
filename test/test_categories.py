from __future__ import annotations

import pytest

from nmr import categories

ROUND_TRIP_CASES = [
    (0, 0, categories.Math.INTEGER),
    (1, 0, categories.Science.ELEMENT),
    (2, 0, categories.Art.MUSIC),
    (6, 0, categories.Commercial.ISBN),
]

NON_ROUND_TRIP_CASES = [
]

ALL_CASES = (
    list(range(16))
    + list(range(n := 109223, n + 32))
    + list(range(n := 3458702354876246, n + 32))
)


def test_simple():
    assert categories.make_category(8) == (categories.Math.FRACTION, 0)


@pytest.mark.parametrize("n,d,t", ROUND_TRIP_CASES)
def test_categories(n, d, t):
    assert t.number_to_index(d) == n
    assert categories.make_category(n) == (t, d)


@pytest.mark.parametrize("n,d,t", NON_ROUND_TRIP_CASES)
def test_categories_non(n, d, t):
    assert (n2 := t.number_to_index(d)) != n
    assert t.number_to_index(n2) == n2
    assert categories.make_category(n) == (t, d)


@pytest.mark.parametrize("n", ALL_CASES)
def test_categories_all(n):
    t, r = categories.make_category(n)
    n2 = t.number_to_index(r)

    assert categories.make_category(n2) == (t, r)
