from __future__ import annotations

import bisect
from collections.abc import Sequence
from pathlib import Path
from typing import Sequence, Iterator
from os import PathLike

from . import count_words, types

# The minimum total number of words needed to be able to represent all 64-bit
# integers with six words or less is 1628
FILE = Path(__file__).parent.parent / "words.txt"


def read_words(file: PathLike[str] | str | None) -> tuple[str, ...]:
    lines = (i.strip() for i in Path(file or FILE).read_text().splitlines())
    return tuple(i for i in lines if i and not i.startswith("#"))


class Nmr:
    """Nmr handles encoding integers to names, and decoding names into integers.

    The exact correspondence depends on the choice and number of words

    """

    COUNT = 1628
    WORDS = read_words(FILE)

    def __init__(
        self,
        count: int | None = None,
        words: Sequence[str] | PathLike[str] | None = None,
    ) -> None:
        if not isinstance(words, (list, tuple)):
            if words is None and count is None:
                count = self.COUNT
                words = self.WORDS
            else:
                words = read_words(words)

        if count is not None:
            words = words[:count]
        assert len(set(words)) == len(words), "Duplicate words"
        self.words = words

        self.count = count_words.CountWords(self.n).count
        self.inverse = {w: i for i, w in enumerate(self.words)}

    def encode_to_name(self, num: int) -> Sequence[str]:
        if num < 0:
            raise ValueError("Only accepts non-negative numbers")
        return [self.words[i] for i in self._to_digits(num)]

    def decode_from_name(self, words: Sequence[str]) -> int:
        words = list(words)
        if len(set(words)) != len(words):
            raise ValueError("Repeated words not allowed")

        try:
            indexes = [self.inverse[w] for w in reversed(words)]
        except KeyError:
            raise KeyError(*sorted(set(words) - set(self.inverse))) from None

        return self._from_digits(list(self._redupe(indexes))[::-1])

    @property
    def n(self) -> int:
        return len(self.words)

    def _to_digits(self, num: int) -> list[int]:
        it = (i + 1 for i in range(self.n) if self.count(i + 1) > num)
        if (word_count := next(it, None)) is None:
            raise ValueError(f"Cannot represent {num} in base {self.n}")

        total = num - self.count(word_count - 1)
        digits = []

        for i in range(word_count):
            total, index = divmod(total, self.n - i)
            digits.append(index)
        assert not total

        return list(self._undupe(digits))[::-1]

    def _from_digits(self, digits: Sequence[int]) -> int:
        total = 0
        for i, d in enumerate(digits):
            total *= self.n - (len(digits) - i - 1)
            total += d

        return self.count(len(digits) - 1) + total

    @staticmethod
    def _undupe(indexes: Sequence[int]) -> Iterator[int]:
        sorted_result: list[int] = []

        for i in indexes:
            for s in sorted_result:
                i += s <= i
            bisect.insort(sorted_result, i)
            yield i

    @staticmethod
    def _redupe(indexes: Sequence[int]) -> Iterator[int]:
        for i, num in enumerate(indexes):
            yield num - sum(k < num for k in indexes[:i])
