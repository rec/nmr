from __future__ import annotations

import bisect
from collections import Counter
from collections.abc import Iterator, Sequence
from os import PathLike
from pathlib import Path
from typing import Any

from . import count_words

# The minimum total number of words needed to be able to represent all 64-bit
# integers with six words or less is 1628
FILE = Path(__file__).parent.parent / "words.txt"
COUNT_FOR_FILE = 1628


class Words:
    """A list of words to use in naming."""

    words: Sequence[str]
    inverse: dict[str, int]
    ignore_case: bool

    def __init__(
        self,
        count: int | None = None,
        words: Sequence[str] | Path | None = None,
        ignore_case: bool = True,
    ) -> None:
        if words is None:
            words = FILE
            if count is None:
                count = COUNT_FOR_FILE

        if isinstance(words, Path):
            with words.open() as fp:
                words = tuple(fp)

        it = (s for w in words if (s := w.strip()) and not s.startswith("#"))
        if ignore_case:
            it = (s.lower() for s in it)
        words = tuple(it)
        _check_dupes(words)

        if count is None:
            count = len(words)
        elif count < len(words):
            words = words[:count]
        elif count > len(words):
            raise ValueError(f"{count=} > {len(words)=}")

        self.words = words
        self.count = count
        self.ignore_case = ignore_case
        self._count_words = count_words.CountWords(self.count)
        self.inverse = {w: i for i, w in enumerate(self.words)}

    def count_words(self, n: int | None = None) -> int:
        return self._count_words.count(n)

    def decode_from_name(self, name: Sequence[str]) -> int:
        name = list(name)
        _check_dupes(name)
        indexes = [self.inverse[w] for w in reversed(name)]
        return self._from_digits(list(_redupe(indexes))[::-1])

    def encode_to_name(self, num: int) -> Sequence[str]:
        if num < 0:
            raise ValueError("Only accepts non-negative numbers")
        return [self.words[i] for i in self._to_digits(num)]

    def is_name(self, s: Sequence[str]) -> bool:
        return all(i in self.inverse for i in s)

    def _to_digits(self, num: int) -> list[int]:
        it = (i + 1 for i in range(self.count) if self.count_words(i + 1) > num)
        if (word_count := next(it, None)) is None:
            raise ValueError(f"Cannot represent {num} in base {self.count}")

        total = num - self.count_words(word_count - 1)
        digits = []

        for i in range(word_count):
            total, index = divmod(total, self.count - i)
            digits.append(index)
        assert not total

        return list(_undupe(digits))[::-1]

    def _from_digits(self, digits: list[int]) -> int:
        total = 0
        for i, d in enumerate(digits):
            total *= self.count - (len(digits) - i - 1)
            total += d

        return self.count_words(len(digits) - 1) + total


def _check_dupes(words: Sequence[str]) -> None:
    if bad := [k for k, v in Counter(words).items() if v > 1]:
        s = "" if len(bad) == 1 else "s"
        msg = ", ".join(sorted(bad))
        raise ValueError(f"Duplicate word{s}: {msg}")


def _redupe(indexes: Sequence[int]) -> Iterator[int]:
    for i, num in enumerate(indexes):
        yield num - sum(k < num for k in indexes[:i])


def _undupe(indexes: Sequence[int]) -> Iterator[int]:
    sorted_result: list[int] = []

    for i in indexes:
        for s in sorted_result:
            i += s <= i
        bisect.insort(sorted_result, i)
        yield i
