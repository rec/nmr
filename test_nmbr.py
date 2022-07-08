from nmbr import COUNT, CountWords, Nmbr
import pytest


@pytest.mark.parametrize('n', (range(1, 7)))
def test_all_unsigned(n):
    N = Nmbr(n, signed=False)
    m = N.count(n)

    for i in range(m):
        words = N(i)
        assert len(words) == len(set(words))
        assert N(words) == i, str(words)

    err = 'Only accepts non-negative numbers'
    with pytest.raises(ValueError, match=err):
        N(-1)

    err = f'Cannot represent {m} in base {n}'
    with pytest.raises(ValueError, match=err):
        N(m)


@pytest.mark.parametrize('n', (range(1, 7)))
def test_all_signed(n):
    N = Nmbr(n)
    m = N.count(n)
    d = (m + 1) // 2
    r = range(d - m, d)

    for i in r:
        words = N(i)
        assert len(words) == len(set(words))
        assert N(words) == i, str(words)

    err = f'Cannot represent {r.start - 1} in base {n}'
    with pytest.raises(ValueError, match=err):
        N(r.start - 1)

    err = f'Cannot represent {r.stop} in base {n}'
    with pytest.raises(ValueError, match=err):
        N(r.stop)


def test_count():
    M = 2 ** 64 - 1

    def count(n, i):
        return CountWords(n)(i)

    assert count(COUNT, 6) > M > count(COUNT - 1, 6)
    assert count(COUNT, 6) > 1.0001 * M
    assert M / 1.003 > count(COUNT - 1, 6)
