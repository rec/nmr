"""Weighted Unicode strings with direct, gapless ranking and unranking."""

import pytest

from nmr.nmr import Nmr
from nmr.types.string import (
    LETTERS,
    SIZE,
    String,
    character_from_index,
    character_index,
)


@pytest.mark.parametrize(
    "value",
    [
        "",
        "a",
        "aa",
        "aaa",
        "dfasdfasdf",
        "Hello, world!",
        "  Keep Case  ",
        "é",
        "e\u0301",
        "🎵日本語",
        "\ud7ff\ue000\U0010ffff",
    ],
)
def test_strings_round_trip_at_each_prefix_scope(value: str) -> None:
    engine = Nmr()
    for scope in [None, "data", ""]:
        result = engine.encode(value, "string", scope)
        assert result.value == value
        assert engine.decode(result.truename).value == value
        assert engine.decode(result.truename, browse=True).value == value


@pytest.mark.parametrize(
    "character,index",
    [
        ("a", 0),
        ("z", 25),
        ("A", 26),
        ("Z", 51),
        (" ", 52),
        ("!", 53),
        ("0", 68),
        ("@", 84),
        ("[", 85),
        ("`", 90),
        ("{", 91),
        ("~", 94),
        ("\xa0", 95),
        ("ÿ", 190),
        ("Ā", 191),
        ("\ud7ff", 55230),
        ("\ue000", 55231),
        ("\U0010ffff", SIZE - 1),
    ],
)
def test_character_order_and_skipped_ranges(character: str, index: int) -> None:
    assert character_index(character) == index
    assert character_from_index(index) == character


def test_string_length_distinguishes_zero_rank_characters() -> None:
    assert [String.str_to_index(i) for i in ["", "a", "aa", "aaa"]] == [0, 1, 53, 2861]


def test_equal_cost_strings_follow_character_order() -> None:
    values = ["aa", "ab", "ac", "ba", "bb", "ca", " ", "!"]
    assert [String.str_to_index(i) for i in values] == [
        53,
        54,
        55,
        105,
        106,
        157,
        2757,
        2758,
    ]


def test_every_string_through_cost_two_has_its_exact_position() -> None:
    expected = [
        "",
        *LETTERS,
        *[a + b for a in LETTERS for b in LETTERS],
        *[character_from_index(i) for i in range(52, 156)],
    ]
    for index, value in enumerate(expected):
        assert String.str_to_index(value) == index
        assert String.index_to_str(index) == value


def test_longer_common_text_precedes_private_use_characters() -> None:
    assert String.str_to_index("helloworld") < String.str_to_index("\ue7da")
    assert String.str_to_index("Z" * 10) < String.str_to_index("\ue7da")


@pytest.mark.parametrize(
    "index", [0, 1, 2, 3, 0xD800, 228965, 2**120, 2**1000, 2**12000]
)
def test_browsing_always_constructs_an_allowed_string(index: int) -> None:
    value = String.index_to_str(index, browse=True)
    assert String.str_to_index(value) == index
    assert String.index_to_str(index) == value
    assert String.index_to_str(String.str_to_index(value)) == value
    assert all(
        ord(i) >= 0x20 and not 0x7F <= ord(i) < 0xA0 and not 0xD800 <= ord(i) < 0xE000
        for i in value
    )


def test_empty_string_has_only_one_index() -> None:
    assert String.index_to_str(0) == ""
    assert String.index_to_str(2, browse=True) == "b"
    assert all(String.index_to_str(i, browse=True) for i in range(1, 3000))


def test_strings_do_not_normalize_case_or_unicode() -> None:
    assert String.str_to_index("Hello") != String.str_to_index("hello")
    assert String.str_to_index("é") != String.str_to_index("e\u0301")


@pytest.mark.parametrize(
    "character", ["\0", "\x1f", "\x7f", "\x80", "\x9f", "\n", "\t", "\ud800", "\udfff"]
)
def test_excluded_characters_are_rejected(character: str) -> None:
    with pytest.raises(ValueError, match="excludes"):
        String.str_to_index(character)


def test_negative_string_indices_are_rejected() -> None:
    with pytest.raises(ValueError, match="nonnegative"):
        String.index_to_str(-1)
