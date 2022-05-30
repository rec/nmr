import itertools
import nmbr
import pytest


@pytest.mark.parametrize('n', (range(1, 7)))
def test_all_simple(n):
    N = nmbr.Nmbr(nmbr.WORDS[:n])
    m = N.count(n)
    for i in range(m):
        words = N(i)
        assert len(words) == len(set(words))
        assert N(words) == i, str(words)

    err = f'Cannot represent {m} in base {n}'
    with pytest.raises(ValueError, match=err):
        N(m)


def old_main():
    N = nmbr.Nmbr(nmbr.WORDS[:6])
    for i in itertools.count():
        try:
            name = N(i)
        except ValueError as e:
            if e.args[0].startswith('Cannot represent'):
                break
            raise
        i2 = N(name)
        digits = N._to_digits(i)
        ud = N._undupe(digits)
        print(
            i, i2, *name,
            '|', *digits,
            '|', *ud,
        )
        assert i == i2
        assert len(name) == len(set(name))
