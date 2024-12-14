from __future__ import annotations

import dataclasses as dc
from enum import IntEnum, auto
from functools import lru_cache


class Category:
    @classmethod
    @lru_cache
    def length(cls) -> int:
        items = list(cls)  # type: ignore
        if items[-1].name == "_RADIX":
            items.pop()
        return len(items)

    @classmethod
    def divmod(cls, n: int, strict: bool = False) -> tuple[int, Category]:
        d, m = divmod(n, cls._RADIX)  # type: ignore[attr-defined]
        if m >= cls.length():
            if strict:
                raise IndexError(f"Out of range {m=}, {cls.length()=}")
            m = m % cls.length()

        self = cls(m + 1)  # type: ignore[call-arg]
        return d, self


class Group(Category, IntEnum):
    MATH = auto()
    SCIENCE = auto()
    MUSIC = auto()
    PLACE = auto()

    TIME = auto()
    NETWORK = auto()
    GAME = auto()
    COMMERCIAL = auto()

    _RADIX = 16


class Subcategory(Category):
    value: int

    def type_to_number(self, n: int) -> int:
        g = Group[self.__class__.__name__.upper()]
        return g.value - 1 + Group._RADIX * (self.value - 1 + self._RADIX * n)

    _RADIX = 8


class Math(Subcategory, IntEnum):
    INTEGER = auto()
    HEX = auto()
    FRACTION = auto()
    FLOATING = auto()


class Science(Subcategory, IntEnum):
    ELEMENT = auto()
    UNIT = auto()


class Music(Subcategory, IntEnum):
    RHYTHM = auto()
    MELODY = auto()


class Place(Subcategory, IntEnum):
    LAT_LONG = auto()


class Time(Subcategory, IntEnum):
    TIME = auto()


class Network(Subcategory, IntEnum):
    IP_ADDRESS = auto()
    SEM_VER = auto()
    UUID = auto()


class Game(Subcategory, IntEnum):
    BACKGAMMON = auto()
    CARDS = auto()
    CHESS = auto()
    GO = auto()


class Commercial(Subcategory, IntEnum):
    ISBN = auto()
    UPC = auto()


def number_to_remainder_and_type(n: int, strict: bool = False) -> tuple[int, Category]:
    d, group = Group.divmod(n, strict)
    name = group.name  # type: ignore[attr-defined]
    subtype = globals()[name.capitalize()]
    result: tuple[int, Category] = subtype.divmod(d, strict)
    return result
