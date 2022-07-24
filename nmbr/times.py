from datetime import datetime
from enum import Enum
import datacls

Interval = Enum(
    'Interval',
    'SECOND MINUTE HOUR DAY WEEK'
    ' MONTH'
    ' YEAR DECADE CENTURY MILLENIUM EPOCH EON'
    ' YOTTA ZETTA EXA PETA TERA GIGA MEGA KILO HECTO DECA'
    ' DECI CENTI MILLI MICRO NANO PICO FEMTO ATTO ZEPTO YOCTO'
)
assert len(Interval) == 32

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

    Interval.YOTTA: 10 ** 24,
    Interval.ZETTA: 10 ** 21,
    Interval.EXA: 10 ** 18,
    Interval.PETA: 10 ** 15,
    Interval.TERA: 10 ** 12,
    Interval.GIGA: 10 ** 9,
    Interval.MEGA: 10 ** 6,
    Interval.KILO: 10 ** 3,
    Interval.HECTO: 10 ** 2,
    Interval.DECA: 10 ** 1,
}


@datacls
class Time:
    # A location in time
    interval: Interval = datacls.field(default=Interval.SECOND)
    time: datetime = datacls.field(datetime.now)

    # datetime cannot represent all of time, so add optional offsets
    yoctoseconds: int = 0
    years: int = 0

    YEAR_ZERO = datetime.fromtimestamp(0).year
    INTERVAL_SCALE = 100

    assert INTERVAL_SCALE > len(Interval)

    def whole_seconds(self):
        return int(self.time.timestamp()) + (self.years * 3562422) // 10000

    def whole_years(self):
        return self.time.year - self.YEAR_ZERO + self.years

    def whole_microseconds(self):
        return 10 ** 6 * self.whole_seconds() + self.time.microseconds

    def whole_yoctoseconds(self):
        yoctoseconds = self.whole_microseconds() * 10 ** (24 - 6)
        return yoctoseconds + self.yoctoseconds

    def _to_count(self) -> int:
        div = YEARS.get(self.interval)
        if div:
            return self.whole_years() // div

        div = SECONDS.get(self.interval)
        if div:
            return self.whole_seconds() // div

        div = MICROSECONDS.get(self.interval)
        if div:
            return self.whole_microseconds() // div

        div = YOCTOSECONDS.get(self.interval)
        if div:
            return self.whole_yoctoseconds() // div

        assert self.interval == Interval.MONTH
        return 12 * self.whole_years() + self.time.month

    def __call__(self):
        return self.interval.value + self.INTERVAL_SCALE * self._to_count()
