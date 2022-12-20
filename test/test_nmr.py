from nmr import COUNT, nmr, Nmr
from nmr.count_words import CountWords
import pytest


def test_count():
    M = 2 ** 64 - 1

    def count(n, i):
        return CountWords(n).count(i)

    assert count(COUNT, 6) > M > count(COUNT - 1, 6)
    assert count(COUNT, 6) > 1.0001 * M
    assert M / 1.003 > count(COUNT - 1, 6)


_STABILITY_TABLE_UNSIGNED = (
    (0, ['the']),
    (1, ['of']),
    (999, ['hans']),
    (134123978423341234, ['this', 'valid', 'menu', 'gamma', 'phase', 'ban']),
    (
        341279384172341314120987134123443434734134913248132481234812341823413,
        [
            'i', 'proud', 'door', 'fight', 'ink', 'later', 'fixed', 'tree',
            'truck', 'bruce', 'taxi', 'play', 'log', 'all', 'res', 'also',
            'cube', 'doing', 'reid', 'cool', 'iron', 'night',
        ]
    ),
)

_STABILITY_TABLE_SIGNED = (
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


@pytest.mark.parametrize('number, words', _STABILITY_TABLE_SIGNED)
def test_stability_signed(number, words):
    nmr = Nmr(signed=True)
    actual_words = nmr(number)
    if actual_words != words:
        print(actual_words)
    assert actual_words == words
    assert nmr(words) == number


@pytest.mark.parametrize('number, words', _STABILITY_TABLE_UNSIGNED)
def test_stability(number, words):
    actual_words = nmr(number)
    if actual_words != words:
        print(actual_words)
    assert actual_words == words
    assert nmr(words) == number
