import itertools

import pytest

from nmr.words import FILE, Words


def test_all_small_permutations_are_bijective() -> None:
    words = ["a", "b", "c", "d", "e"]
    engine = Words(words)
    indices = set()
    for n in range(1, len(words) + 1):
        for p in itertools.permutations(words, n):
            index = engine.from_truename(p)
            assert engine.to_truename(index) == list(p)
            indices.add(index)
    assert indices == set(range(engine.count_words()))


@pytest.mark.parametrize(
    "words", [[], ["a", "A"], ["two words"], ["a:b"], ["e\u0301", "é"]]
)
def test_invalid_vocabularies_are_rejected(words: list[str]) -> None:
    with pytest.raises(ValueError):
        Words(words)


@pytest.mark.parametrize("truename", [[], ["one", "one"], ["missing"]])
def test_invalid_truenames_are_rejected(truename: list[str]) -> None:
    with pytest.raises(ValueError):
        Words(["one", "two"]).from_truename(truename)


def test_vocabulary_identity_covers_order_case_policy_and_unicode() -> None:
    first = Words(["e\u0301", "A"])
    second = Words(["é", "a"])
    assert first.identifier == second.identifier
    assert first.identifier != Words(["a", "é"]).identifier
    assert first.identifier != Words(["é", "a"], ignore_case=False).identifier
    assert Words(first.export().splitlines()).identifier == first.identifier


@pytest.mark.parametrize(
    "before,word,after",
    [
        ("for", "is", "on"),
        ("at", "as", "your"),
        ("which", "news", "out"),
        ("click", "its", "like"),
        ("human", "yes", "hot"),
    ],
)
def test_restored_words_follow_google_frequency_order(
    before: str, word: str, after: str
) -> None:
    words = Words().words
    position = words.index(word)
    assert words[position - 1 : position + 2] == (before, word, after)


@pytest.mark.parametrize(
    "following, article",
    [
        ("alpha", "an"),
        ("egg", "an"),
        ("in", "an"),
        ("of", "an"),
        ("use", "an"),
        ("stand", "a"),
        ("home", "a"),
    ],
)
def test_bundled_article_spelling_roundtrips(following: str, article: str) -> None:
    engine = Words()
    index = engine.from_truename(["a", following])
    assert engine.to_truename(index) == [article, following]
    assert engine.from_truename([article, following]) == index
    assert engine.to_truename(engine.from_truename(["a"])) == ["a"]
    assert "an" not in engine.words
    assert not engine.is_truename(["a", "an"])
    with pytest.raises(ValueError, match="repeat"):
        engine.from_truename(["a", "an"])


def test_custom_vocabulary_keeps_literal_articles() -> None:
    engine = Words(["a", "an", "alpha"])
    for words in [["a", "alpha"], ["an", "alpha"], ["a", "an"]]:
        assert engine.to_truename(engine.from_truename(words)) == words
    bundled = Words()
    assert Words(FILE, count=bundled.count).identifier == bundled.identifier
    assert bundled.identifier != Words(bundled.words).identifier
