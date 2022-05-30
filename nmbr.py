from pathlib import Path
import bisect
import functools
import xmod
from typing import Sequence, Union

COUNT = 1628
FILE = Path(__file__).parent / 'words.txt'
WORDS = tuple(i.strip() for i in FILE.read_text().splitlines())


class Nmbr:
    def __init__(self, words=WORDS):
        assert len(set(words)) == len(words), 'Duplicate words'
        self.words = words
        self.inverse = {w: i for i, w in enumerate(words)}
        self.limit = self.n ** self.n

    def __call__(self, s: Union[int, Sequence[str]]):
        return self.to_name(s) if isinstance(s, int) else self.to_int(s)

    def to_name(self, num: int) -> Sequence[str]:
        return [self.words[i] for i in self._to_digits(num)]

    def to_int(self, words: Sequence[str]):
        indexes = [self.inverse[w] for w in reversed(words)]
        return self._from_digits(list(self._redupe(indexes))[::-1])

    @property
    def n(self):
        return len(self.words)

    @functools.lru_cache()
    def perms(self, c):
        if c <= 0:
            return 1
        return (self.n - c + 1) * self.perms(c - 1)

    @functools.lru_cache()
    def count(self, c):
        if c <= 0:
            return 0
        return self.perms(c) + self.count(c - 1)

    def _to_digits(self, num):
        it = (i + 1 for i in range(self.n) if self.count(i + 1) > num)
        if (word_count := next(it, None)) is None:
            raise ValueError(f'Cannot represent {num} in base {self.n}')

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
    def _redupe(indexes):
        for i, num in enumerate(indexes):
            yield num - sum(k < num for k in indexes[:i])

    @staticmethod
    def _undupe(indexes):
        sorted_result = []

        for i in indexes:
            for s in sorted_result:
                i += (s <= i)
            bisect.insort(sorted_result, i)
            yield i


nmbr = xmod(Nmbr())


def main(count=32):
    import random
    import sys

    for i in range(count):
        r = random.randint(0, sys.maxsize)
        print(f'{r}:', *nmbr(r))


if __name__ == '__main__':
    main()
