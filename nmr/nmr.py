from __future__ import annotations

import bisect
from collections import Counter
from collections.abc import Iterator, Sequence
from os import PathLike
from pathlib import Path
from typing import Any

from . import types
from .words import Words


class Nmr:
    """Nmr handles encoding integers to names, and decoding names into integers.

    The exact correspondence depends on the choice and number of words
    """

    def __init__(
        self,
        words: Sequence[str] | Path | None = None,
        count: int | None = None,
        ignore_case: bool = True,
    ) -> None:
        self.words = Words(words, count, ignore_case)

    def name_to_str(self, name: Sequence[str]) -> str:
        index = self.words.decode_from_name(name)
        return types.index_to_str(index)

    def str_to_name(self, s: str) -> Sequence[str]:
        index = types.str_to_index(s)
        return self.words.encode_to_name(index)

    def convert(self, s: str) -> str:
        if self.words.is_name(split := s.split()):
            return self.name_to_str(split)
        return " ".join(self.str_to_name(s))
