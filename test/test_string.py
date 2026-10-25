"""Letter-first characters, diagonal tuples, and distinct string lengths."""

import pytest

from nmr.nmr import Nmr
from nmr.pack_numbers import Packer
from nmr.types.string import SIZE, String, character_from_index, character_index


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
        assert engine.decode(result.name).value == value
        assert engine.decode(result.name, browse=True).value == value


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
    assert [String.str_to_index(i) for i in ["", "a", "aa", "aaa"]] == [0, 1, 3, 7]


def test_equal_length_strings_follow_diagonal_order() -> None:
    values = ["aa", "ba", "ab", "ca", "bb", "ac"]
    assert [String.str_to_index(i) for i in values] == [3, 11, 19, 27, 35, 43]


def test_common_letters_produce_short_names() -> None:
    name = Nmr().encode("dfasdfasdf", "string").name
    assert len(name.partition(":")[2].split()) <= 5


@pytest.mark.parametrize("index", [0, 1, 2, 3, 0xD800, 2**120, 2**1000])
def test_browsing_always_constructs_an_allowed_string(index: int) -> None:
    value = String.index_to_str(index, browse=True)
    assert String.index_to_str(String.str_to_index(value)) == value
    assert all(
        ord(i) >= 0x20 and not 0x7F <= ord(i) < 0xA0 and not 0xD800 <= ord(i) < 0xE000
        for i in value
    )


def test_browsing_wraps_out_of_range_characters_and_repairs_empty_aliases() -> None:
    index = ((2 * Packer(count=2).pack(SIZE, 1) + 1) << 2) - 1
    with pytest.raises(ValueError, match="canonical domain"):
        String.index_to_str(index)
    assert String.index_to_str(index, browse=True) == "ab"
    with pytest.raises(ValueError, match="Noncanonical empty"):
        String.index_to_str(2)
    assert String.index_to_str(2, browse=True) == ""


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
