from nmr import COUNT, nmr
from nmr.count_words import CountWords
import pytest


def test_count():
    M = 2 ** 64 - 1

    def count(n, i):
        return CountWords(n).count(i)

    assert count(COUNT, 6) > M > count(COUNT - 1, 6)
    assert count(COUNT, 6) > 1.0001 * M
    assert M / 1.003 > count(COUNT - 1, 6)


_STABILITY_TABLE = (
    (0, ['the']),
    (1, ['and']),
    (-1, ['of']),
    (-2, ['to']),
    (999, ['the', 'asia']),
    (-32000, ['but', 'null']),
    (134123978423341234, ['all', 'shed', 'earn', 'level', 'goat', 'throw']),
    (
        -341279384172341314120987134123443434734134913248132481234812341823413,
        [
            'an', 'coach', 'drum', 'drive', 'after', 'chad', 'gem', 'kent',
            'event', 'taxes', 'mark', 'trip', 'icon', 'site', 'focus', 'real',
            'wide', 'foam', 'gone', 'pine', 'mild', 'egg',
        ]
    ),
)


@pytest.mark.parametrize('number, words', _STABILITY_TABLE)
def test_stability(number, words):
    actual_words = nmr(number)
    if actual_words != words:
        print(actual_words)
    assert actual_words == words
    assert nmr(words) == number
