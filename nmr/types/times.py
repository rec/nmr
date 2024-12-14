from __future__ import annotations

import dataclasses as dc
from datetime import datetime
from enum import IntEnum, auto
from typing import cast

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


@dc.dataclass
class Time:
    # A location in time
    interval: Interval = dc.field(default=Interval.SECOND)
    time: datetime = dc.field(default_factory=datetime.now)

    # datetime cannot represent all of time, so add optional offsets
    yoctoseconds: int = 0
    years: int = 0

    YEAR_ZERO = datetime.fromtimestamp(0).year
    INTERVAL_SCALE = 100

    assert INTERVAL_SCALE > len(Interval)

    def whole_seconds(self) -> int:
        return int(self.time.timestamp()) + (self.years * 3562422) // 10000

    def whole_years(self) -> int:
        return self.time.year - self.YEAR_ZERO + self.years

    def whole_microseconds(self) -> int:
        return 10**6 * self.whole_seconds() + self.time.microsecond

    def whole_yoctoseconds(self) -> int:
        yoctoseconds = self.whole_microseconds() * MICROSECOND_TO_YOCTOSECOND
        return yoctoseconds + self.yoctoseconds

    def _to_count(self) -> int:
        if div := YEARS.get(self.interval, 0):
            return self.whole_years() // div

        if div := SECONDS.get(self.interval, 0):
            return self.whole_seconds() // div

        if div := MICROSECONDS.get(self.interval, 0):
            return self.whole_microseconds() // div

        if div := YOCTOSECONDS.get(self.interval, 0):
            # TODO(rec): why is only this cast needed?
            return cast(int, self.whole_yoctoseconds() // div)

        assert self.interval == Interval.MONTH
        return 12 * self.whole_years() + self.time.month

    def __call__(self) -> int:
        return self.interval.value + self.INTERVAL_SCALE * self._to_count()
