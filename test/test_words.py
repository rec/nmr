import itertools

import pytest

from nmr.words import Words


def test_all_small_permutations_are_bijective() -> None:
    words = ["a", "b", "c", "d", "e"]
    engine = Words(words)
    indices = set()
    for n in range(1, len(words) + 1):
        for p in itertools.permutations(words, n):
            index = engine.decode_from_name(p)
            assert engine.encode_to_name(index) == list(p)
            indices.add(index)
    assert indices == set(range(engine.count_words()))


@pytest.mark.parametrize(
    "words", [[], ["a", "A"], ["two words"], ["a:b"], ["e\u0301", "é"]]
)
def test_invalid_vocabularies_are_rejected(words: list[str]) -> None:
    with pytest.raises(ValueError):
        Words(words)


@pytest.mark.parametrize("name", [[], ["one", "one"], ["missing"]])
def test_invalid_names_are_rejected(name: list[str]) -> None:
    with pytest.raises(ValueError):
        Words(["one", "two"]).decode_from_name(name)


def test_vocabulary_identity_covers_order_case_policy_and_unicode() -> None:
    first = Words(["e\u0301", "A"])
    second = Words(["é", "a"])
    assert first.identifier == second.identifier
    assert first.identifier != Words(["a", "é"]).identifier
    assert first.identifier != Words(["é", "a"], ignore_case=False).identifier
    assert Words(first.export().splitlines()).identifier == first.identifier
