from __future__ import annotations

import dataclasses as dc
from enum import IntEnum, auto
from functools import lru_cache
from typing import Type, cast

from typing_extensions import Self

DEFAULT_RADIX = 8


class Category:
    name: str
    value: int

    @classmethod
    def divmod(cls, n: int, strict: bool = False) -> tuple[Category, int]:
        d, m = divmod(n, cls.radix())
        lc = len(cls)  # type: ignore[arg-type]
        if m >= lc:
            if strict:
                raise IndexError(f"Out of range {m=}, len(cls)={lc}")
            m = m % lc

        self = cls(m + 1)  # type: ignore[call-arg]
        return self, d

    @classmethod
    def radix(cls) -> int:
        return _RADIX_TABLE.get(cls, DEFAULT_RADIX)  # type: ignore[arg-type]

    SUBCLASSES: dict[str, Type[Category]] = {}

    def __init_subclass__(cls) -> None:
        assert cls.__name__ not in cls.SUBCLASSES
        cls.SUBCLASSES[cls.__name__] = cls


class Group(Category, IntEnum):
    MATH = auto()
    SCIENCE = auto()
    ART = auto()
    LOCATION = auto()

    COMPUTER = auto()
    GAME = auto()
    COMMERCIAL = auto()
    COMBINE = auto()


class Subcategory(Category):
    def number_to_index(self, n: int) -> int:
        g = Group[self.__class__.__name__.upper()]
        return g.value - 1 + Group.radix() * (self.value - 1 + self.radix() * n)


class Math(Subcategory, IntEnum):
    INTEGER = auto()
    FRACTION = auto()
    FLOATING = auto()


class Science(Subcategory, IntEnum):
    ELEMENT = auto()
    UNIT = auto()
    SMILES = auto()


class Art(Subcategory, IntEnum):
    MUSIC = auto()


class Location(Subcategory, IntEnum):
    LAT_LONG = auto()
    TIME = auto()


class Computer(Subcategory, IntEnum):
    IP_V4_ADDRESS = auto()
    IP_V6_ADDRESS = auto()
    SEMVER = auto()
    UUID = auto()


class Game(Subcategory, IntEnum):
    BACKGAMMON = auto()
    CARDS = auto()
    CHESS = auto()
    GO = auto()


class Commercial(Subcategory, IntEnum):
    ISBN = auto()
    UPC = auto()


class Combine(Subcategory, IntEnum):
    COMBINE = auto()


_RADIX_TABLE = {Location: 4, Computer: 32, Commercial: 32, Combine: 1}


def make_category(n: int, strict: bool = False) -> tuple[Category, int]:
    group, d = Group.divmod(n, strict)
    subclass = Category.SUBCLASSES[group.name.capitalize()]
    return subclass.divmod(d, strict)
