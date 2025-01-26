import itertools

import pytest

from nmr.words import Words

WORD_LISTS = (
    ("one", "two", "three"),
    ("one", "two", "Three"),
    ("one", "Two", "three", "Three"),
)

PARAMS = itertools.product(WORD_LISTS, (False, True))


@pytest.mark.parametrize("words, ignore_case", PARAMS)
def test_case(words, ignore_case):
    try:
        try:
            w = Words(words, ignore_case=ignore_case)
        except ValueError as e:
            if words == ("one", "Two", "three", "Three") and ignore_case:
                assert e.args == ("Duplicate word: three",)
                return
            else:
                raise

        expected = 4
        name = w.encode_to_name(expected)
        actual = w.decode_from_name(name)
        assert actual == expected

        original = "one", "Three"
        expected = ("one", "three") if ignore_case else original
        n = w.decode_from_name(original)
        if len(words) == 4:
            assert name == ["Two", "one"]
        else:
            assert name == ["one", "two"]
        try:
            actual = w.encode_to_name(n)
        except ValueError as e:
            if words == ("one", "two", "three") and not ignore_case:
                assert e.args == ("Didn't recognize the following word: Three",)
                return
            else:
                raise

        assert actual == list(expected)

    except ValueError as e:
        if words == ("one", "two", "three") and not ignore_case:
            assert e.args == ("Didn't recognize the following word: Three",)
