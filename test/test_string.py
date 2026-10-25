"""Strings have exact identity and a total inverse over Unicode scalar text."""

import pytest

from nmr.nmr import Nmr
from nmr.types.string import String


@pytest.mark.parametrize(
    "value",
    [
        "",
        "Hello, world!",
        "  Keep Case  ",
        "é",
        "e\u0301",
        "🎵日本語",
        "\0\n\t",
        "\ud7ff\ue000\U0010ffff",
    ],
)
def test_strings_preserve_every_character_at_each_prefix_scope(value: str) -> None:
    engine = Nmr()
    for scope in [None, "data", ""]:
        result = engine.encode(value, "string", scope)
        assert result.value == value
        assert engine.decode(result.name).value == value
        assert engine.decode(result.name, browse=True).value == value


@pytest.mark.parametrize("index", [0, 1, 0xD800, 0xD801, 0x10F800, 2**120, 2**1000])
def test_every_index_decodes_to_a_canonical_string(index: int) -> None:
    value = String.index_to_str(index)
    assert String.str_to_index(value) == index
    assert String.index_to_str(index, browse=True) == value
    assert not any(0xD800 <= ord(i) < 0xE000 for i in value)


def test_strings_do_not_normalize_case_or_unicode() -> None:
    assert String.str_to_index("Hello") != String.str_to_index("hello")
    assert String.str_to_index("é") != String.str_to_index("e\u0301")


def test_invalid_unicode_and_negative_indices_are_rejected() -> None:
    with pytest.raises(ValueError, match="Unicode scalar"):
        String.str_to_index("\ud800")
    with pytest.raises(ValueError, match="nonnegative"):
        String.index_to_str(-1)
