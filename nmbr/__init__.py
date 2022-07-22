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
import sys
import threading
import uuid

__all__ = 'Convert', 'Nmbr', 'WORDS', 'count', 'nmbr', 'try_to_int'
__version__ = '0.8.0'

# The minimum total number of words needed to be able to represent all 64-bit
# signed integers with six words or less is 1628
COUNT = 1628
FILE = Path(__file__).parent.parent / 'words.txt'
WORDS = tuple(i.strip() for i in FILE.read_text().splitlines())[:COUNT]
VERSION_DIGIT = 1024
DEGREE_DIVISIONS = 100000000
DEGREE_MULTIPLIER = 1000 * DEGREE_DIVISIONS


def read_words(file=None):
    lines = (i.strip() for i in Path(file or FILE).read_text().splitlines())
    return tuple(i for i in lines if i)


class Nmbr:
    COUNT = 1628

    def __init__(self, count=None, words=None, signed=True):
        if not isinstance(words, (list, tuple)):
            if words is None and count is None:
                count = self.COUNT
            words = read_words(words)

        if count is not None:
            words = words[:count]
        assert len(set(words)) == len(words), 'Duplicate words'
        self.words = words

        self.signed = signed
        self.count = CountWords(self.n)
        self.inverse = {w: i for i, w in enumerate(self.words)}

    def __call__(self, st: Union[int, Sequence[str], str]):
        s = try_to_int(st)
        if s is None:
            raise ValueError(f'Do not understand {st}, {type(st)}')

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


class Convert:
    class Integer:
        to_int = staticmethod(int)
        from_int = staticmethod(str)

    class Hex:
        @staticmethod
        def to_int(s: str):
            s = s.lower()
            if s.startswith('0x'):
                return int(s[2:], 16)
            if s.startswith('-0x'):
                return -int(s[2:], 16)

        from_int = staticmethod(hex)

    class Semver:
        BASE = 1024

        @classmethod
        def to_int(cls, s: str) -> Optional[int]:
            s2 = s[1:] if s.startswith('v') else s
            p = [int(i) for i in s2.split('.')]
            if len(p) == 3 and all(i < cls.BASE for i in p):
                v = p[2] + cls.BASE * (p[1] + cls.BASE * p[0])
                return v * cls.BASE

        @classmethod
        def from_int(cls, i: int) -> Optional[str]:
            if i >= 0:
                d0, m0 = divmod(i, cls.BASE)
                if not m0:
                    d1, m1 = divmod(d0, cls.BASE)
                    d2, m2 = divmod(d1, cls.BASE)
                    d3, m3 = divmod(d2, cls.BASE)
                    if not d3:
                        return f'v{m3}.{m2}.{m1}'

    class LatLong:
        DIVISIONS = 100000000  # Each degree is divided by ten million
        MULT = 100000 * DIVISIONS  # Means a gap of two zeros between numbers

        @classmethod
        def to_int(cls, s: str) -> Optional[int]:
            from lat_long_parser import parse

            lat, lon = (parse(i) for i in s.split(','))
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                lat = round(cls.DIVISIONS * (lat + 90))
                lon = round(cls.DIVISIONS * (lon + 180))
                return lon + cls.MULT * lat

        @classmethod
        def from_int(cls, i: int) -> Optional[str]:
            from lat_long_parser import to_str_deg_min_sec

            lat, lon = divmod(i, cls.MULT)
            lat = lat / cls.DIVISIONS - 90
            lon = lon / cls.DIVISIONS - 180

            if -90 <= lat <= 90 and -180 <= lon <= 180:
                lat = to_str_deg_min_sec(lat)
                lon = to_str_deg_min_sec(lon)

                if lat.startswith('-'):
                    lat, ns = lat[1:], 'S'
                else:
                    ns = 'N'

                if lon.startswith('-'):
                    lat, ew = lat[1:], 'W'
                else:
                    ew = 'E'

                lat += ' ' * (' ' in lat) + ns
                lon += ' ' * (' ' in lon) + ew

                return f'{lat}, {lon}'

    class IpAddress:
        @staticmethod
        def to_int(s: str) -> Optional[int]:
            return int(ipaddress.ip_address(s))

        @staticmethod
        def from_int(i: int) -> Optional[str]:
            return str(ipaddress.ip_address(i))

    class UUID:
        @staticmethod
        def to_int(s: str) -> Optional[int]:
            if len(s) == 36 and s.count('-') == 4:
                return uuid.UUID(s)

        @staticmethod
        def from_int(i: int) -> Optional[str]:
            return str(uuid.UUID(int=i))

    CLASSES = Integer, Hex, Semver, LatLong, IpAddress, UUID

    @classmethod
    def to_int(cls, s: str) -> Optional[int]:
        for c in cls.CLASSES:
            try:
                i = c.to_int(s)
            except Exception:
                pass
            else:
                if i is not None:
                    return i


def try_to_int(s: str) -> Union[int, str]:
    i = Convert.to_int(s)
    return s if i is None else i


# TODO: bring in the other end of the conversions from nmbr_main
# TODO: times/dates
# TODO: phone numbers?
# TODO: chess positions
# TODO: go positions

nmbr = Nmbr()
nmbr.__dict__.update(globals())

sys.modules[__name__] = nmbr


if __name__ == '__main__':
    from . import __main__

    __main__.main()
