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
    to_type = types.Fraction.int_to_type
    actual = [str(to_type(i)) for i in range(16)]
    expected = ['0', '0', '2', '-2', '1/2', '-1/2', '3', '-3', '1', '-1', '1/3', '-1/3', '4', '-4', '3/2', '-3/2']
    assert actual == expected

    actual = [str(to_type(i)) for i in range(16)]
    expected = ['0', '0', '2', '-2', '1/2', '-1/2', '3', '-3', '1', '-1', '1/3', '-1/3', '4', '-4', '3/2', '-3/2']
    assert actual == expected
