"""
🔢 ``nmbr``: memorable names for large numbers 🔢

EXAMPLE
=========

.. code-block:: python

    import nmbr

    assert nmbr(0) == ['the']
    assert nmbr(2718281828) == ['the', 'race', 'tie', 'hook']

    for i in range(-2, 3):
        print(i, *nmbr(i))

    # Prints
    #   -2 to
    #   -1 of
    #   0 the
    #   1 and
    #   2 a

"""

from pathlib import Path
import bisect
import threading
import xmod
from typing import Optional, Sequence, Union

__all__ = 'Nmbr', 'WORDS', 'nmbr'

# The minimum total number of words needed to be able to represent all 64-bit
# integers with six words or less is 1628
COUNT = 1628
FILE = Path(__file__).parent / 'words.txt'
WORDS = tuple(i.strip() for i in FILE.read_text().splitlines())[:COUNT]


class Nmbr:
    def __init__(self, words=COUNT, signed=True):
        if isinstance(words, int):
            self.words = WORDS[:words]
        else:
            self.words = list(words)
        assert len(set(self.words)) == len(self.words), 'Duplicate words'

        self.signed = signed
        self.count = CountWords(self.n)
        self.inverse = {w: i for i, w in enumerate(self.words)}

    def __call__(self, s: Union[int, Sequence[str], str]):
        if isinstance(s, int):
            return self.to_name(s)

        if isinstance(s, str):
            return self.to_int(s.split())

        return self.to_int(s)

    def to_name(self, num: int) -> Sequence[str]:
        original = num
        if self.signed:
            num = abs(num * 2) - (num < 0)
        elif num < 0:
            raise ValueError('Only accepts non-negative numbers')
        return [self.words[i] for i in self._to_digits(num, original)]

    def to_int(self, words: Sequence[str]):
        assert len(set(words)) == len(words), 'Repeated words not allowed'

        try:
            indexes = [self.inverse[w] for w in reversed(words)]
        except KeyError:
            raise KeyError(*sorted(set(words) - set(self.inverse))) from None

        value = self._from_digits(list(self._redupe(indexes))[::-1])
        if not self.signed:
            return value

        num, negative = divmod(value, 2)
        return -num - 1 if negative else num

    @property
    def n(self):
        return len(self.words)

    def _to_digits(self, num, original):
        it = (i + 1 for i in range(self.n) if self.count(i + 1) > num)
        if (word_count := next(it, None)) is None:
            raise ValueError(f'Cannot represent {original} in base {self.n}')

        total = num - self.count(word_count - 1)
        digits = []

        for i in range(word_count):
            total, index = divmod(total, self.n - i)
            digits.append(index)
        assert not total

        return list(self._undupe(digits))[::-1]

    def _from_digits(self, digits):
        total = 0
        for i, d in enumerate(digits):
            total *= self.n - (len(digits) - i - 1)
            total += d

        return self.count(len(digits) - 1) + total

    @staticmethod
    def _undupe(indexes):
        sorted_result = []

        for i in indexes:
            for s in sorted_result:
                i += (s <= i)
            bisect.insort(sorted_result, i)
            yield i

    @staticmethod
    def _redupe(indexes):
        for i, num in enumerate(indexes):
            yield num - sum(k < num for k in indexes[:i])


class CountWords:
    def __init__(self, n):
        self.n = n
        self._perm_count = [(1, 0)]
        self._lock = threading.Lock()

    def __call__(self, c: int) -> int:
        if len(self._perm_count) - 1 < c:
            with self._lock:
                perm, count = self._perm_count[-1]

                for i in range(len(self._perm_count) - 1, c):
                    perm *= self.n - i
                    count += perm
                    self._perm_count.append((perm, count))

        return self._perm_count[c][1]

    @classmethod
    def count(cls, n: int, c: Optional[int] = None) -> int:
        if c is None:
            c = n
        return cls(n)(c)


nmbr = xmod(Nmbr())


def main():
    import random
    import sys

    argv = sys.argv[1:]
    if argv:
        for a in argv:
            print(f'{a}:', *nmbr(int(a)))
    else:
        for i in range(32):
            r = random.randint(0, sys.maxsize)
            print(f'{r}:', *nmbr(r))


if __name__ == '__main__':
    main()
