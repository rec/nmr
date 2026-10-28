from itertools import permutations
from math import comb, factorial
from random import Random

import pytest

from nmr.nmr import Nmr
from nmr.recognition import describe_input
from nmr.types.cards import Cards, completions, rank_permutation, unrank_permutation


@pytest.mark.parametrize("size", range(8))
def test_every_small_deck_has_exactly_one_rank_in_displacement_order(size: int) -> None:
    ordered = sorted(
        permutations(range(size)),
        key=lambda p: (
            sum(i != n for i, n in enumerate(p)),
            tuple(i for i, n in enumerate(p) if i != n),
            tuple(n for i, n in enumerate(p) if i != n),
        ),
    )
    for index, permutation in enumerate(ordered):
        assert rank_permutation(list(permutation)) == index
        assert unrank_permutation(index, size) == list(permutation)


@pytest.mark.parametrize(
    "index,value",
    [
        (0, "()"),
        (1, "(1 2)"),
        (2, "(1 3)"),
        (51, "(1 52)"),
        (52, "(2 3)"),
        (1326, "(51 52)"),
        (1327, "(1 2 3)"),
        (1328, "(1 3 2)"),
        (45527, "(1 2) (3 4)"),
    ],
)
def test_early_decks_have_short_cycle_descriptions(index: int, value: str) -> None:
    assert Cards.index_to_str(index) == value
    assert Cards.str_to_index(value) == index


def test_every_displacement_group_has_the_expected_boundaries() -> None:
    offset = 1
    for moved in range(2, 53):
        count = comb(52, moved) * completions(moved, moved)
        for index in [offset, offset + count - 1]:
            permutation = unrank_permutation(index, 52)
            assert sum(i != n for i, n in enumerate(permutation)) == moved
            assert rank_permutation(permutation) == index
        offset += count
    assert offset == factorial(52)


def test_large_indices_round_trip_and_the_last_deck_is_reversed() -> None:
    random = Random(417)
    for index in [random.randrange(factorial(52)) for _ in range(100)]:
        assert Cards.str_to_index(Cards.index_to_str(index)) == index
    last = " ".join(f"({i} {53 - i})" for i in range(1, 27))
    assert Cards.index_to_str(factorial(52) - 1) == last


@pytest.mark.parametrize(
    "value,canonical",
    [("( )", "()"), ("(2 1)", "(1 2)"), ("(4 3)(2 1)", "(1 2) (3 4)")],
)
def test_cycle_rotation_order_and_spacing_are_normalized(
    value: str, canonical: str
) -> None:
    assert Cards.index_to_str(Cards.str_to_index(value)) == canonical


@pytest.mark.parametrize(
    "value",
    [
        "",
        "[]",
        "(1)",
        "(0 2)",
        "(1 53)",
        "(1 1)",
        "(1 2)(2 3)",
        "(a b)",
        "(1,2)",
        "(1 2) trailing",
        "((1 2))",
        "() (1 2)",
    ],
)
def test_invalid_cycle_descriptions_are_rejected(value: str) -> None:
    with pytest.raises(ValueError):
        Cards.str_to_index(value)


def test_browsing_wraps_after_all_decks_but_canonical_decoding_rejects_overflow() -> (
    None
):
    for index in [-1, factorial(52), factorial(52) + 1]:
        with pytest.raises(ValueError):
            Cards.index_to_str(index)
    assert Cards.index_to_str(factorial(52), browse=True) == "()"
    assert Cards.index_to_str(factorial(52) + 1, browse=True) == "(1 2)"
    with pytest.raises(ValueError):
        Cards.index_to_str(-1, browse=True)


@pytest.mark.parametrize("permutation", [[0, 0], [1, 2], [-1, 0]])
def test_permutation_rank_rejects_missing_or_repeated_cards(
    permutation: list[int],
) -> None:
    with pytest.raises(ValueError):
        rank_permutation(permutation)


@pytest.mark.parametrize("value", ["()", "(1 2)", "(1 2 3)", "(1 2) (3 4)"])
def test_cards_are_recognized_and_round_trip_through_the_type_tree(value: str) -> None:
    engine = Nmr()
    assert engine.find_type("cards")[0] == "play:game:cards"
    result = describe_input(value, engine)
    assert result.kind == "cards"
    assert engine.decode(result.truename).value == value
    for scope in [None, "", "play", "game"]:
        encoded = engine.encode(value, "cards", scope)
        assert engine.decode(encoded.truename).value == value
        assert engine.decode(encoded.truename, browse=True).canonical


@pytest.mark.parametrize("value", ["(", "(1 ", "(1 2) ("])
def test_incomplete_cycles_wait_for_more_input(value: str) -> None:
    assert describe_input(value, Nmr()).truename is None
