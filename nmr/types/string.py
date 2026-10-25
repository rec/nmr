"""Exact Unicode strings, enumerated without invalid surrogate code points."""

from ..pack_numbers import rank_digits, unrank_digits
from ..type_namer import TypeNamer


class String(TypeNamer):
    label = "string"
    description = "Exact Unicode text, preserving case and whitespace"

    @staticmethod
    def str_to_index(value: str) -> int:
        digits = []
        for character in value:
            code = ord(character)
            if 0xD800 <= code < 0xE000:
                raise ValueError("String requires Unicode scalar values")
            digits.append(code - 0x800 if code >= 0xE000 else code)
        return rank_digits(digits, BASE)

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        return "".join(
            chr(i + 0x800 if i >= 0xD800 else i) for i in unrank_digits(index, BASE)
        )


BASE = 0x110000 - 0x800
