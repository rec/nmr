from scripts.remove_homophones import without_homophones


def test_homophone_filter_retains_the_first_word_in_vocabulary_order() -> None:
    words = ["sea", "keep", "see", "bee", "be"]
    assert without_homophones(words, [["see", "sea"], ["be", "bee", "missing"]]) == [
        "sea",
        "keep",
        "bee",
    ]
