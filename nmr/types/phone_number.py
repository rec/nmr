"""
https://github.com/google/libphonenumber/blob/master/FALSEHOODS.md

Let's assume that:

* phone numbers start with + or * or are numbers with dashes (which are ignored)
* possible digits within the number are 0-9, +, *, #
* stretch goal: handle 1-800-MATTRESS

"""

from __future__ import annotations

import fractions
import math
from typing import Any

from ..category import Commercial
from ..type_namer import TypeNamer

DIGITS = "0123456789"
STARTERS = "+*#"
DIVIDERS = " -"
LEGAL = set(DIGITS + STARTERS + DIVIDERS)


class PhoneNumber:
    def __init__(self, phone_number: str) -> None:
        if phone_number and phone_number[0] not in STARTERS:
            raise ValueError(f"{phone_number=} must start with one of {STARTERS=}")


class PhoneNumber(TypeNamer[str]):
    category = Commercial.PHONE_NUMBER

    @staticmethod
    def index_to_type(i: int) -> Version:
        return Version(*packer.unpack(i))

    @staticmethod
    def str_to_type(s: str) -> Version:
        if s.startswith("v"):
            return Version.parse(s[1:])
        raise ValueError("semantic versions must start with v")

    @staticmethod
    def type_to_index(v: Version) -> int:
        return packer.pack(v.major, v.minor, v.patch)

    @staticmethod
    def type_to_str(v: Version) -> str:
        return f"v{v}"
