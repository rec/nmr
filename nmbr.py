#!/usr/bin/env python3

"""
🔢 ``nmbr``: memorable names for large numbers 🔢

Convert an integer, even a very long one, into a short list of common, short
non-repeating English words... or use a word list of your choice.

Installs both a module named ``nmbr`` and an executable called ``nmbr.py``

EXAMPLE
=========

.. code-block:: python

    import nmbr

    assert nmbr(0) == ['the']
    assert nmbr(2718281828) == ['the', 'race', 'tie', 'hook']

    for i in range(-2, 3):
        print(i, ':', *nmbr(i))

    # Prints
    #   -2 : to
    #   -1 : of
    #   0 : the
    #   1 : and
    #   2 : a

"""
from functools import cached_property
from pathlib import Path
from typing import Optional, Sequence, Union
import bisect
import ipaddress
import threading
import xmod

__all__ = 'Nmbr', 'WORDS', 'count', 'nmbr', 'try_to_int'
__version__ = '0.8.0'

# The minimum total number of words needed to be able to represent all 64-bit
# signed integers with six words or less is 1628
COUNT = 1628
FILE = Path(__file__).parent / 'words.txt'
WORDS = tuple(i.strip() for i in FILE.read_text().splitlines())[:COUNT]


def read_words(file=None):
    lines = (i.strip() for i in Path(file or FILE).read_text().splitlines())
    return tuple(i for i in lines if i)


class Nmbr:
    def __init__(self, count=None, words=None, signed=True):
        if not isinstance(words, (list, tuple)):
            if words is None and count is None:
                count = COUNT
            words = read_words(words)

        if count is not None:
            words = words[:count]
        assert len(set(words)) == len(words), 'Duplicate words'
        self.words = words

        self.signed = signed
        self.count = CountWords(self.n)
        self.inverse = {w: i for i, w in enumerate(self.words)}

    def __call__(self, s: Union[int, Sequence[str], str]):
        import nmbr

        s = nmbr.try_to_int(s)

        if isinstance(s, int):
            return self.int_to_name(s)

        if isinstance(s, str):
            return self.name_to_int(s.split())

        return self.name_to_int(s)

    def int_to_name(self, num: int) -> Sequence[str]:
        original = num
        if self.signed:
            num = abs(num * 2) - (num < 0)
        elif num < 0:
            raise ValueError('Only accepts non-negative numbers')
        return [self.words[i] for i in self._to_digits(num, original)]

    def name_to_int(self, words: Sequence[str]) -> int:
        words = list(words)
        if len(set(words)) != len(words):
            raise ValueError('Repeated words not allowed')

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

    @cached_property
    def maxint(self):
        return self.count() // 2 - 1 if self.signed else self.count() - 1

    @cached_property
    def minint(self):
        return -self.count() // 2 if self.signed else 0

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

    def __call__(self, c: Optional[int] = None) -> int:
        if c is None:
            c = self.n

        if len(self._perm_count) - 1 < c:
            with self._lock:
                perm, count = self._perm_count[-1]

                for i in range(len(self._perm_count) - 1, c):
                    perm *= self.n - i
                    count += perm
                    self._perm_count.append((perm, count))

        return self._perm_count[c][1]


def try_to_int(s):
    try:
        return int(s)
    except Exception:
        pass
    try:
        if s.lower().startswith('0x'):
            return int(s[2:], 16)
    except Exception:
        pass
    try:
        return int(ipaddress.ip_address(s))
    except Exception:
        pass
    return s


nmbr = xmod(Nmbr())
count = nmbr.count


if __name__ == '__main__':
    import nmbr_main

    nmbr_main.main()
