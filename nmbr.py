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
import xmod

__all__ = 'Nmbr', 'WORDS', 'count', 'nmbr'
__version__ = '0.8.0'

# The minimum total number of words needed to be able to represent all 64-bit
# signed integers with six words or less is 1628
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
        s = try_to_int(s)

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


USAGE = """
`nmbr` is a Python module which uniquely names every number, including
IP addresses and hex numbers.

USAGE:

    nmbr [-i/--ip-address] [-x/--hex] <num-or-name>] [... <num-or-name>]
        Converts numbers to names or vice

    nmbr -h/--help - prints this message


"""


def main():
    import itertools
    import random

    def usage(errorcode=0):
        print(USAGE, sys.stderr)
        sys.exit(errorcode)

    to_hex = to_ip_address = False

    args = []
    for a in sys.argv[1:]:
        ar = a.rstrip('-')
        if not (a.startswith('-') or a[1:].isnumeric()):
            args.append(a)
        elif ar in ('h', 'help'):
            usage()
        elif ar in ('x', 'hex'):
            to_hex = True
        elif ar in ('i', 'ip-address'):
            to_ip_address = True
        else:
            print('Unknown flag', a, file=sys.stderr)
            usage(True)

    if to_hex and to_ip_address:
        msg = 'At most one of -i/--ip-address and -x/--hex may be set'
        print(msg, file=sys.stderr)
        usage(True)

    def convert_lines():
        items = itertools.chain(group_args(), stdin_lines())
        return sum(convert(i) or 1 for i in items)

    def convert(i):
        try:
            if isinstance(i, int):
                print(i, ':', *nmbr(i))
            else:
                print(*i, ':', to_int(i))
        except Exception as e:
            print('ERROR:', e, file=sys.stderr)

    def rnd():
        for i in range(128):
            r = int(10 ** random.uniform(0, 50))
            print(f'{r}:', *nmbr(r))

    def is_int(s):
        return isinstance(s, int)

    def group_args():
        iargs = (try_to_int(a) for a in args)
        for num, it in itertools.groupby(iargs, is_int):
            yield from it if num else [list(it)]

    def stdin_lines():
        if sys.stdin.isatty():
            return

        for line in (line for i in sys.stdin if (line := i.strip())):
            parts = [try_to_int(s) for s in line.split()]
            nums = sum(is_int(i) for i in parts)
            if nums == 0:
                yield parts
            elif nums == len(parts):
                yield from parts
            else:
                msg = f'Line mixes numbers and words: "{line}"'
                print(msg, file=sys.stderr)

    def to_int(i):
        n = nmbr(i)
        if to_hex:
            return hex(n)
        if to_ip_address:
            try:
                return str(ipaddress.ip_address(n))
            except Exception:
                pass
        return str(n)

    convert_lines() or rnd()


nmbr = xmod(Nmbr())
count = nmbr.count


if __name__ == '__main__':
    main()
