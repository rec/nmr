import itertools

import pytest

from nmr.pack_numbers import Packer

ROUND_TRIPS = (
    [0],
    [10],
    [0, 0],
    [4, 7],
    [0, 0, 0],
    [2, 7, 3],
    [0, 0, 0, 0],
    [0, 2, 0, 1],
)
PARAMS = itertools.product(ROUND_TRIPS, [False, True])


@pytest.mark.parametrize("numbers, forward", PARAMS)
def test_round_trip(numbers, forward):
    p = Packer(len(numbers), forward)
    result = p.unpack(p.pack(*numbers))
    assert result == numbers
