from nmbr import COUNT, nmbr
from nmbr.count_words import CountWords


def test_count():
    M = 2 ** 64 - 1

    def count(n, i):
        return CountWords(n)(i)

    assert count(COUNT, 6) > M > count(COUNT - 1, 6)
    assert count(COUNT, 6) > 1.0001 * M
    assert M / 1.003 > count(COUNT - 1, 6)


def test_stability():
    debug = not True
    if debug:
        print('_STABILITY_TABLE = (')

    for number, words in _STABILITY_TABLE:
        if debug:
            names = "', '".join(nmbr(number))
            print(f'    ({number}, [\'{names}\']),')
        else:
            actual_words = nmbr(number)
            if actual_words != words:
                print(actual_words)
            assert actual_words == words
            assert nmbr(words) == number

    if debug:
        print(')')

    assert not debug


_STABILITY_TABLE = (
    (0, ['the']),
    (1, ['and']),
    (-1, ['of']),
    (-2, ['to']),
    (999, ['the', 'feed']),
    (-32000, ['has', 'lab']),
    (134123978423341234, ['as', 'moms', 'wet', 'myth', 'hose', 'joint']),
    (
        -341279384172341314120987134123443434734134913248132481234812341823413,
        [
            'new', 'comes', 'tube', 'wan', 'sofa', 'vast', 'geek', 'grey',
            'cop', 'final', 'upon', 'prev', 'foot', 'time', 'store', 'full',
            'bad', 'coal', 'pink', 'era', 'sept', 'dose',
        ]
    ),
)
