from __future__ import annotations

import bisect
from collections import Counter
from collections.abc import Iterator, Sequence
from os import PathLike
from pathlib import Path
from typing import Any

from . import count_words, types

# The minimum total number of words needed to be able to represent all 64-bit
# integers with six words or less is 1628
FILE = Path(__file__).parent.parent / "words.txt"
COUNT_FOR_FILE = 1628


class Nmr:
    """Nmr handles encoding integers to names, and decoding names into integers.

    The exact correspondence depends on the choice and number of words

    """

    COUNT = 1628

    words: Sequence[str]
    inverse: dict[str, int]

    def __init__(
        self,
        count: int | None = None,
        words: Sequence[str] | Path | None = None,
    ) -> None:
        if words is None:
            words = FILE
            if count is None:
                count = COUNT_FOR_FILE

        if isinstance(words, Path):
            with words.open() as fp:
                words = tuple(fp)

        words = tuple(s for w in words if (s := w.strip()) and not s.startswith("#"))
        _check_dupes(words)

        if count is not None:
            if count > len(words):
                raise ValueError(f"{count=} > {len(words)=}")
            words = words[:count]

        self.words = words
        self._count_words = count_words.CountWords(self.n).count
        self.inverse = {w: i for i, w in enumerate(self.words)}

    def is_name(self, s: Sequence[str]) -> bool:
        return all(i in self.inverse for i in s)

    def name_to_type(self, name: Sequence[str]) -> str:
        index = self._decode_from_name(name)
        return types.index_to_str(index)

    def type_to_name(self, type: Sequence[str]) -> str:
        index = types.str_to_index(" ".join(type))
        return " ".join(self._encode_to_name(index))

    def convert(self, s: Sequence[str]) -> str:
        return self.name_to_type(s) if self.is_name(s) else self.type_to_name(s)

    @property
    def n(self) -> int:
        return len(self.words)

    def _encode_to_name(self, num: int) -> Sequence[str]:
        if num < 0:
            raise ValueError("Only accepts non-negative numbers")
        return [self.words[i] for i in self._to_digits(num)]

    def _decode_from_name(self, name: Sequence[str]) -> int:
        name = list(name)
        _check_dupes(name)
        indexes = [self.inverse[w] for w in reversed(name)]
        return self._from_digits(list(self._redupe(indexes))[::-1])

    def _to_digits(self, num: int) -> list[int]:
        it = (i + 1 for i in range(self.n) if self._count_words(i + 1) > num)
        if (word_count := next(it, None)) is None:
            raise ValueError(f"Cannot represent {num} in base {self.n}")

        total = num - self._count_words(word_count - 1)
        digits = []

        for i in range(word_count):
            total, index = divmod(total, self.n - i)
            digits.append(index)
        assert not total

        return list(self._undupe(digits))[::-1]

    def _from_digits(self, digits: list[int]) -> int:
        total = 0
        for i, d in enumerate(digits):
            total *= self.n - (len(digits) - i - 1)
            total += d

        return self._count_words(len(digits) - 1) + total

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


def _check_dupes(words: Sequence[str]) -> None:
    if bad := [k for k, v in Counter(words).items() if v > 1]:
        s = "" if len(bad) == 1 else "s"
        msg = ", ".join(sorted(bad))
        raise ValueError(f"Duplicate word{s}: {msg}")
