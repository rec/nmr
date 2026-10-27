from itertools import permutations, product
from math import comb

import pytest

from nmr.pack_numbers import Packer, pair, unpair


@pytest.mark.parametrize("count", [1, 2, 3, 8])
def test_arbitrary_precision_packing(count: int) -> None:
    numbers = [10**100 + i for i in range(count)]
    packer = Packer(count=count)
    assert packer.unpack(packer.pack(*numbers)) == numbers


@pytest.mark.parametrize("count", [1, 2, 3, 4])
def test_sum_layers_are_contiguous_and_bijective(count: int) -> None:
    packer = Packer(count=count)
    for total in range(6):
        tuples = [i for i in product(range(total + 1), repeat=count) if sum(i) == total]
        ranks = [packer.pack(*i) for i in tuples]
        assert sorted(ranks) == list(
            range(comb(total + count - 1, count), comb(total + count, count))
        )
        for values, rank in zip(tuples, ranks, strict=True):
            assert packer.unpack(rank) == list(values)


def test_triples_follow_the_agreed_order() -> None:
    packer = Packer(count=3)
    expected = [
        [0, 0, 0],
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
        [2, 0, 0],
        [1, 1, 0],
        [1, 0, 1],
        [0, 2, 0],
        [0, 1, 1],
        [0, 0, 2],
    ]
    for rank, values in enumerate(expected):
        assert packer.pack(*values) == rank
        assert packer.unpack(rank) == values
    assert packer.pack(2, 1, 3) == 69
    assert packer.unpack(69) == [2, 1, 3]


def test_pairs_keep_the_existing_enumeration() -> None:
    packer = Packer(count=2)
    for x, y in product([0, 1, 7, 10**100], repeat=2):
        assert packer.pack(x, y) == pair(x, y)
        assert packer.unpack(pair(x, y)) == [x, y]


def test_unbalanced_tuples_share_the_same_sum_layer() -> None:
    packer = Packer(count=3)
    total = 10**100 + 3
    for values in permutations([10**100, 1, 2]):
        rank = packer.pack(*values)
        assert comb(total + 2, 3) <= rank < comb(total + 3, 3)
        assert packer.unpack(rank) == list(values)


def test_large_tuples_can_pack_zeroes_and_single_units() -> None:
    packer = Packer(count=256)
    assert packer.pack(*([0] * 256)) == 0
    assert packer.unpack(0) == [0] * 256
    assert packer.pack(*([0] * 255 + [1])) == 256
    assert packer.unpack(256) == [0] * 255 + [1]


@pytest.mark.parametrize("count", [3, 8, 64])
def test_large_arbitrary_indices_round_trip(count: int) -> None:
    packer = Packer(count=count)
    for rank in [2**64 - 1, 2**64, 2**1024 + 17]:
        values = packer.unpack(rank)
        assert len(values) == count
        assert all(i >= 0 for i in values)
        assert packer.pack(*values) == rank


def test_invalid_packing_inputs_are_rejected() -> None:
    packer = Packer(count=3)
    with pytest.raises(ValueError):
        packer.pack(1, 2)
    with pytest.raises(ValueError):
        packer.pack(1, -1, 2)
    with pytest.raises(ValueError):
        packer.unpack(-1)


def test_pair_boundaries() -> None:
    for d in [0, 1, 10, 10**30, 10**300]:
        boundary = d * (d + 1) // 2
        for n in range(max(0, boundary - 1), boundary + 2):
            assert pair(*unpair(n)) == n
