"""Rank and unrank nonempty word permutations, without repeated words."""

import bisect
import hashlib
import json
import unicodedata
from collections.abc import Sequence
from functools import cached_property
from pathlib import Path

from .count_words import CountWords

FILE = Path(__file__).with_name("words.txt")
COUNT_FOR_FILE = 1628


class Words:
    def __init__(
        self,
        words: Sequence[str] | Path | None = None,
        count: int | None = None,
        ignore_case: bool = True,
    ) -> None:
        self.ignore_case = ignore_case
        if words is None:
            words = FILE
            if count is None:
                count = COUNT_FOR_FILE
        if isinstance(words, Path):
            words = words.read_bytes().decode().splitlines()
        tokens = [
            self.normalize(i.strip())
            for i in words
            if i.strip() and not i.lstrip().startswith("#")
        ]
        if not tokens or any(":" in i or any(c.isspace() for c in i) for i in tokens):
            raise ValueError(
                "A vocabulary needs nonempty words without whitespace or colons"
            )
        if len(tokens) != len(set(tokens)):
            raise ValueError("Duplicate words after vocabulary normalization")
        if count is not None:
            if not 1 <= count <= len(tokens):
                raise ValueError("Word count must be between 1 and the vocabulary size")
            tokens = tokens[:count]
        self.words = tuple(tokens)
        self.count = len(tokens)
        self.inverse = {w: i for i, w in enumerate(tokens)}
        self._counts = CountWords(self.count)

    def normalize(self, word: str) -> str:
        word = unicodedata.normalize("NFC", word)
        return (
            unicodedata.normalize("NFC", word.casefold()) if self.ignore_case else word
        )

    @cached_property
    def identifier(self) -> str:
        contents = json.dumps(
            ["nmr-vocabulary-1", self.ignore_case, self.words],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return hashlib.sha256(contents.encode()).hexdigest()

    def export(self) -> str:
        return "\n".join(self.words) + "\n"

    def count_words(self, n: int | None = None) -> int:
        if n is not None and not 0 <= n <= self.count:
            raise ValueError("Word length outside vocabulary capacity")
        return self._counts.count(n)

    def encode_to_name(self, num: int) -> list[str]:
        if num < 0:
            raise ValueError("Only accepts non-negative numbers")
        length = next(
            (i for i in range(1, self.count + 1) if self.count_words(i) > num), None
        )
        if length is None:
            raise ValueError("Vocabulary capacity exceeded; choose a larger word list")
        total = num - self.count_words(length - 1)
        digits: list[int] = []
        used: list[int] = []
        for i in range(length):
            total, digit = divmod(total, self.count - i)
            for index in used:
                digit += index <= digit
            bisect.insort(used, digit)
            digits.append(digit)
        return [self.words[i] for i in reversed(digits)]

    def decode_from_name(self, name: Sequence[str]) -> int:
        words = [self.normalize(i) for i in name]
        if not words:
            raise ValueError("A name needs at least one word")
        if len(words) != len(set(words)):
            raise ValueError("A name cannot repeat words")
        unknown = [i for i in words if i not in self.inverse]
        if unknown:
            raise ValueError("Unrecognized words: " + ", ".join(unknown))
        indexes = [self.inverse[i] for i in reversed(words)]
        digits = [n - sum(i < n for i in indexes[:j]) for j, n in enumerate(indexes)]
        total = 0
        for i, digit in enumerate(reversed(digits)):
            total = total * (self.count - len(digits) + i + 1) + digit
        return self.count_words(len(words) - 1) + total

    def is_name(self, words: Sequence[str]) -> bool:
        tokens = [self.normalize(i) for i in words]
        return (
            bool(tokens)
            and len(tokens) == len(set(tokens))
            and all(i in self.inverse for i in tokens)
        )
