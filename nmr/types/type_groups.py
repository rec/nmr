from enum import IntEnum, auto
from functools import lru_cache


class Type:
    @classmethod
    @lru_cache()
    def length(cls):
        items = list(cls)
        if items[-1].name == 'RADIX':
            items.pop()
        return len(items)

    @classmethod
    def divmod(cls, n: int, strict=False):
        d, m = divmod(n, cls.RADIX)
        if m >= cls.length():
            if strict:
                raise IndexError(f'Out of range {m=}, {cls.length()=}')
            m = m % cls.length()

        print('divmod', cls, n, d, m)
        return d, cls(m + 1)

    RADIX = 8

    def type_to_number(self, n):
        g = Group[self.__class__.__name__.lower()]
        return g.value - 1 + Group.RADIX * (self.value - 1 + self.RADIX * n)


class Group(Type, IntEnum):
    math = auto()
    science = auto()
    music = auto()
    place = auto()

    time = auto()
    network = auto()
    game = auto()
    commercial = auto()

    RADIX = 16


class Math(Type, IntEnum):
    integer = auto()
    fraction = auto()
    floating = auto()


class Science(Type, IntEnum):
    element = auto()
    unit = auto()


class Music(Type, IntEnum):
    rhythm = auto()
    melody = auto()


class Place(Type, IntEnum):
    lat_long = auto()


class Time(Type, IntEnum):
    instant = auto()


class Network(Type, IntEnum):
    ip_address = auto()
    sem_ver = auto()
    uuid = auto()


class Game(Type, IntEnum):
    backgammon = auto()
    cards = auto()
    chess = auto()
    go = auto()


class Commercial(Type, IntEnum):
    isbn = auto()
    upc = auto()


def number_to_remainder_and_type(n, strict=False):
    d, group = Group.divmod(n, strict)
    subtype = globals()[group.name.capitalize()]
    return subtype.divmod(d, strict)
