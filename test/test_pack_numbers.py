import pytest

from nmr.pack_numbers import Packer, pair, unpair


@pytest.mark.parametrize("count", [1, 2, 3, 8])
@pytest.mark.parametrize("forward", [False, True])
def test_arbitrary_precision_packing(count: int, forward: bool) -> None:
    numbers = [10**100 + i for i in range(count)]
    packer = Packer(count=count, forward=forward)
    assert packer.unpack(packer.pack(*numbers)) == numbers


def test_pair_boundaries() -> None:
    for d in [0, 1, 10, 10**30, 10**300]:
        boundary = d * (d + 1) // 2
        for n in range(max(0, boundary - 1), boundary + 2):
            assert pair(*unpair(n)) == n
