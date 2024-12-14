from __future__ import annotations

from enum import IntEnum, auto
from functools import lru_cache


class Category:
    @classmethod
    @lru_cache
    def length(cls) -> int:
        items = list(cls)  # type: ignore
        if items[-1].name == "RADIX":
            items.pop()
        return len(items)

    @classmethod
    def divmod(cls, n: int, strict: bool = False) -> tuple[int, Category]:
        d, m = divmod(n, cls.RADIX)
        if m >= cls.length():
            if strict:
                raise IndexError(f"Out of range {m=}, {cls.length()=}")
            m = m % cls.length()

        return d, cls(m + 1)

    RADIX = 8

    def type_to_number(self, n: int) -> int:
        g = Group[self.__class__.__name__.upper()]
        return g.value - 1 + Group.RADIX * (self.value - 1 + self.RADIX * n)


class Group(Category, IntEnum):
    MATH = auto()
    SCIENCE = auto()
    MUSIC = auto()
    PLACE = auto()

    TIME = auto()
    NETWORK = auto()
    GAME = auto()
    COMMERCIAL = auto()

    RADIX = 16


class Math(Category, IntEnum):
    INTEGER = auto()
    HEX = auto()
    FRACTION = auto()
    FLOATING = auto()


class Science(Category, IntEnum):
    ELEMENT = auto()
    UNIT = auto()


class Music(Category, IntEnum):
    RHYTHM = auto()
    MELODY = auto()


class Place(Category, IntEnum):
    LAT_LONG = auto()


class Time(Category, IntEnum):
    TIME = auto()


class Network(Category, IntEnum):
    IP_ADDRESS = auto()
    SEM_VER = auto()
    UUID = auto()


class Game(Category, IntEnum):
    BACKGAMMON = auto()
    CARDS = auto()
    CHESS = auto()
    GO = auto()


class Commercial(Category, IntEnum):
    ISBN = auto()
    UPC = auto()


def number_to_remainder_and_type(n, strict=False):
    d, group = Group.divmod(n, strict)
    subtype = globals()[group.name.capitalize()]
    return subtype.divmod(d, strict)
