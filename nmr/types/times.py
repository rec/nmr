from __future__ import annotations

import dataclasses as dc
from datetime import datetime
from enum import IntEnum, auto
from typing import cast

from ._time_constants import (
    MICROSECOND_TO_YOCTOSECOND,
    MICROSECONDS,
    SECONDS,
    YEARS,
    YOCTOSECONDS,
    Interval,
)


@dc.dataclass
class Time:
    # A location in time
    interval: Interval = dc.field(default=Interval.SECOND)
    time: datetime = dc.field(default_factory=datetime.now)

    # datetime cannot represent all of time, so add optional offsets
    yoctoseconds: int = 0
    years: int = 0

    YEAR_ZERO = datetime.fromtimestamp(0).year
    INTERVAL_SCALE = len(Interval)

    def whole_seconds(self) -> int:
        # TODO: this is only approximate.
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
