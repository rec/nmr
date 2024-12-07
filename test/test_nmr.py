from nmr import nmr, Nmr
from nmr.count_words import CountWords
import pytest


def test_count():
    M = 2 ** 64 - 1

    def count(n, i):
        return CountWords(n).count(i)

    assert count(Nmr.COUNT, 6) > M > count(Nmr.COUNT - 1, 6)
    assert count(Nmr.COUNT, 6) > 1.0001 * M
    assert M / 1.003 > count(Nmr.COUNT - 1, 6)


_STABILITY_TABLE = (
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


@pytest.mark.parametrize('number, words', _STABILITY_TABLE)
def test_stability(number, words):
    actual_words = nmr.int_to_name(number)
    if actual_words != words:
        print(actual_words)
    assert actual_words == words
    assert nmr.name_to_int(words) == number
