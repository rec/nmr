from enum import IntEnum, auto

MICROSECOND_TO_YOCTOSECOND: int = 10 ** (24 - 6)


class Interval(IntEnum):
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

    YOTTASECOND = auto()
    ZETTASECOND = auto()
    EXASECOND = auto()
    PETASECOND = auto()
    TERASECOND = auto()
    GIGASECOND = auto()
    MEGASECOND = auto()
    KILOSECOND = auto()
    HECTOSECOND = auto()
    DECASECOND = auto()

    DECISECOND = auto()
    CENTISECOND = auto()
    MILLISECOND = auto()
    MICROSECOND = auto()
    NANOSECOND = auto()
    PICOSECOND = auto()
    FEMTOSECOND = auto()
    ATTOSECOND = auto()
    ZEPTOSECOND = auto()
    YOCTOSECOND = auto()


SCALES = {
    Interval.YEAR: {
        Interval.YEAR: 1,
        Interval.DECADE: 10,
        Interval.CENTURY: 100,
        Interval.MILLENIUM: 1000,
        Interval.EPOCH: 1_000_000,
        Interval.EON: 1_000_000_000,
    },
    Interval.SECOND: {
        Interval.SECOND: 1,
        Interval.MINUTE: 60,
        Interval.HOUR: 60 * 60,
        Interval.DAY: 60 * 60 * 24,
        Interval.WEEK: 60 * 60 * 24 * 7,
        Interval.DECASECOND: 10**1,
        Interval.HECTOSECOND: 10**2,
        Interval.KILOSECOND: 10**3,
        Interval.MEGASECOND: 10**6,
        Interval.GIGASECOND: 10**9,
        Interval.TERASECOND: 10**12,
        Interval.PETASECOND: 10**15,
        Interval.EXASECOND: 10**18,
        Interval.ZETTASECOND: 10**21,
        Interval.YOTTASECOND: 10**24,
    },
    Interval.MICROSECOND: {
        Interval.DECISECOND: 100_000,
        Interval.CENTISECOND: 10_000,
        Interval.MILLISECOND: 1_000,
        Interval.MICROSECOND: 1,
    },
    Interval.YOCTOSECOND: {
        Interval.NANOSECOND: 10 ** (24 - 9),
        Interval.PICOSECOND: 10 ** (24 - 12),
        Interval.FEMTOSECOND: 10 ** (24 - 15),
        Interval.ATTOSECOND: 10 ** (24 - 18),
        Interval.ZEPTOSECOND: 10 ** (24 - 21),
        Interval.YOCTOSECOND: 10 ** (24 - 24),
    },
}

assert set(i for s in SCALES.values() for i in s.values()) == set(Interval)
