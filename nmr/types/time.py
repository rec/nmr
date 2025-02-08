from __future__ import annotations

import dataclasses as dc
from datetime import datetime
from enum import IntEnum, auto
from typing import cast

from ._time_constants import MICROSECOND_TO_YOCTOSECOND, SCALES, Interval


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

    def _to_count(self) -> int:
        for interval, scale in SCALES.items():
            if div := scale.get(self.interval, 0):
                break
        else:
            assert False, f"Bad {self.interval=}"
        count = cast(int, getattr(self, f"_whole_{interval.name.lower()}s") // div)
        return self.interval.value + self.INTERVAL_SCALE * count

    def _whole_seconds(self) -> int:
        # TODO: this is only approximate.
        return int(self.time.timestamp()) + (self.years * 3562422) // 10000

    def _whole_years(self) -> int:
        return self.time.year - self.YEAR_ZERO + self.years

    def _whole_microseconds(self) -> int:
        return 10**6 * self._whole_seconds() + self.time.microsecond

    def _whole_yoctoseconds(self) -> int:
        yoctoseconds = self._whole_microseconds() * MICROSECOND_TO_YOCTOSECOND
        return yoctoseconds + self.yoctoseconds

    def _whole_months(self) -> int:
        return 12 * self._whole_years() + self.time.month
