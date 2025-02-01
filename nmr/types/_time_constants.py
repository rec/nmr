from enum import IntEnum, auto

MICROSECOND_TO_YOCTOSECOND: int = 10 ** (24 - 6)


class Interval(IntEnum):
    INSTANT = auto()

    SECOND = auto()
    MINUTE = auto()
    HOUR = auto()
    DAY = auto()
    WEEK = auto()
    MONTH = auto()
    YEAR = auto()
    DECADE = auto()
    CENTURY = auto()
    MILLENIUM = auto()
    EPOCH = auto()
    EON = auto()

    YOTTA = auto()
    ZETTA = auto()
    EXA = auto()
    PETA = auto()
    TERA = auto()
    GIGA = auto()
    MEGA = auto()
    KILO = auto()
    HECTO = auto()
    DECA = auto()

    DECI = auto()
    CENTI = auto()
    MILLI = auto()
    MICRO = auto()
    NANO = auto()
    PICO = auto()
    FEMTO = auto()
    ATTO = auto()
    ZEPTO = auto()
    YOCTO = auto()


MICROSECONDS = {
    Interval.DECI: 100000,
    Interval.CENTI: 10000,
    Interval.MILLI: 1000,
    Interval.MICRO: 1,
}

YOCTOSECONDS = {
    Interval.NANO: 10 ** (24 - 9),
    Interval.PICO: 10 ** (24 - 12),
    Interval.FEMTO: 10 ** (24 - 15),
    Interval.ATTO: 10 ** (24 - 18),
    Interval.ZEPTO: 10 ** (24 - 21),
    Interval.YOCTO: 10 ** (24 - 24),
}

YEARS = {
    Interval.YEAR: 1,
    Interval.DECADE: 10,
    Interval.CENTURY: 100,
    Interval.MILLENIUM: 1000,
    Interval.EPOCH: 1000000,
    Interval.EON: 1000000000,
}

SECONDS = {
    Interval.INSTANT: 0,
    Interval.SECOND: 1,
    Interval.MINUTE: 60,
    Interval.HOUR: 60 * 60,
    Interval.DAY: 60 * 60 * 24,
    Interval.WEEK: 60 * 60 * 24 * 7,
    Interval.DECA: 10**1,
    Interval.HECTO: 10**2,
    Interval.KILO: 10**3,
    Interval.MEGA: 10**6,
    Interval.GIGA: 10**9,
    Interval.TERA: 10**12,
    Interval.PETA: 10**15,
    Interval.EXA: 10**18,
    Interval.ZETTA: 10**21,
    Interval.YOTTA: 10**24,
}
