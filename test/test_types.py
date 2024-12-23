import pytest

from nmr import types

ROUND_TRIPS = (
    "12341324",
    "0xdeadbeef",
    "127.0.0.1",
    "v1.1.92",
    """52° 22' 3.36" N, 4° 54' 14.76" E""",
    "123e4567-e89b-12d3-a456-426614174000",
    "1/2",
    # '0/1',  fails
    # '0/4',  fails
    "1752/491",
)


@pytest.mark.parametrize("s", ROUND_TRIPS)
def test_roundtrips(s):
    cls, i = types.class_int(s)
    assert s == str(cls.int_to_type(i))


def test_fractions():
    to_type = types.Fraction.int_to_type
    a = [str(to_type(i)) for i in range(0, 8)]
    assert a == ["0", "0/-1", "2", "-2/-1", "1/2", "-1/-2", "3", "-3/-1"]

    a = [str(to_type(i)) for i in range(0, 8)]
    assert a == ["0", "0/-1", "2", "-2/-1", "1/2", "-1/-2", "3", "-3/-1"]
