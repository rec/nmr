from pathlib import Path
from . count_words import CountWords
from functools import cached_property
from . convert import try_to_int
from typing import Sequence, Union
import bisect

# The minimum total number of words needed to be able to represent all 64-bit
# signed integers with six words or less is 1628
COUNT = 1628
FILE = Path(__file__).parent.parent / 'words.txt'


class Nmbr:
    COUNT = 1628
    WORDS = tuple(i.strip() for i in FILE.read_text().splitlines())

    def __init__(self, count=None, words=None, signed=True):
        if not isinstance(words, (list, tuple)):
            if words is None and count is None:
                count = self.COUNT
                words = self.WORDS
            else:
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


def read_words(file=None):
    lines = (i.strip() for i in Path(file or FILE).read_text().splitlines())
    return tuple(i for i in lines if i)
