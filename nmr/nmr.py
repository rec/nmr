from __future__ import annotations

from collections.abc import Sequence

from . import types
from .words import Words


class Nmr(Words):
    """Nmr handles encoding integers to names, and decoding names into integers.

    The exact correspondence depends on the choice and number of words
    """

    def name_to_str(self, name: Sequence[str]) -> str:
        """Given a name, a sequence of strings from `self.words`"""
        index = self.decode_from_name(name)
        return types.index_to_str(index)

    def str_to_name(self, s: str) -> Sequence[str]:
        index = types.str_to_index(s)
        return self.encode_to_name(index)

    def convert(self, s: str) -> str:
        if self.is_name(split := s.split()):
            return self.name_to_str(split)
        return " ".join(self.str_to_name(s))
