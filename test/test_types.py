import pytest

from nmr import types

ROUND_TRIPS = (
    "12341324",
    # "0xdeadbeef",
    # "127.0.0.1",
    # "v1.1.92",
    # """52° 22' 3.36" N, 4° 54' 14.76" E""",
    # "123e4567-e89b-12d3-a456-426614174000",
    # "1/2",
    # # '0/1',  fails
    # # '0/4',  fails
    # "1752/491",
)


@pytest.mark.parametrize("s", ROUND_TRIPS)
def test_roundtrips(s):
    i = types.str_to_index(s)
    assert s == types.index_to_str(i)


def test_fractions():
    to_type = [types.Fraction.index_to_type(i) for i in range(32)]
    actual = [str(i) for i in to_type]
    expected1 = (
        ['0'] +
        ['1', '-1'] +
        ['1/2', '2', '-1/2'] +
        ['1/3', '-2', '1', '-1/3'] +
        ['1/4', '3', '-1', '2/3', '-1/4'] +
        ['1/5', '-3', '3/2', '-2/3', '1/2', '-1/5'] +
        ['1/6', '4', '-3/2', '1', '-1/2', '2/5', '-1/6', '1/7'] +
        ['-4', '2', '-1']
    )
    assert actual == expected1
    actual = [types.Fraction.type_to_index(t) for t in to_type]
    expected2 = (
        [0] +
        [1, 2] +
        [3, 4, 5] +
        [6, 7, 1, 9] +
        [10, 11, 2, 13, 14] +
        [15, 16, 17, 18, 3, 20] +
        [21, 22, 23, 1, 5, 26, 27, 28] +
        [29, 4, 2]
    )
    assert actual == expected2

    actual = [str(types.Fraction.index_to_type(i)) for i in expected2]
    assert actual == expected1
