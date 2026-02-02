from __future__ import annotations
from ...type_namer import TypeNamer

import dataclasses as dc
from datetime import datetime
from enum import IntEnum, auto
from typing import cast

from . import formats
from .constants import MICROSECOND_TO_YOCTOSECOND, SCALES, Interval, INVERSE_SCALES

YEAR_ZERO = datetime.fromtimestamp(0).year
INTERVAL_SCALE = len(Interval)


@dc.dataclass
class Time(TypeNamer["Time"]):
    # A location in time
    interval: Interval = dc.field(default=Interval.SECOND)
    time: datetime = dc.field(default_factory=datetime.now)

    # datetime cannot represent all of time, so add optional offsets
    yoctoseconds: int = 0
    years: int = 0

    YEAR_ZERO = datetime.fromtimestamp(0).year
    INTERVAL_SCALE = len(Interval)

    __str__ = formats.to_string
    str_to_type = staticmethod(from_string)

    @staticmethod
    def index_to_type(i: int) -> "Time":
        count, interval = divmod(i, INTERVAL_SCALE)
        _base = INVERSE_SCALES[interval]
        raise NotImplementedError

    def __int__(self) -> int:
        for base, scale in SCALES.items():
            if div := scale.get(self.interval, 0):
                break
        else:
            raise ValueError(f"Logic error: {self=}, {locals()=}")

        if base == Interval.SECONDS:
            count = self._whole_seconds()
        elif base == Interval.MONTHS:
            count = self._whole_months()
        elif base == Interval.YEARS:
            count = self._whole_years()
        elif base == Interval.MICROSECONDS:
            count = self._whole_microseconds()
        elif base == Interval.YOCTOSECONDS:
            count = self._whole_yoctoseconds()
        else:
            raise ValueError(f"Logic error: {self=}, {locals()=}")

        return self.interval + self.INTERVAL_SCALE * count * div

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


@dc.dataclass
class Time(TypeNamer["Time"]):
    # A location in time
    interval: Interval = dc.field(default=Interval.SECOND)
    time: datetime = dc.field(default_factory=datetime.now)

    # datetime cannot represent all of time, so add optional offsets
    yoctoseconds: int = 0
    years: int = 0

    def __str__(self) -> str:
        raise NotImplementedError  # todo

    @staticmethod
    def str_to_type(cls, s: str) -> "Time": ...

    @staticmethod
    def index_to_type(cls, i: int) -> "Time":
        count, interval = divmod(i, INTERVAL_SCALE)
        if interval == Interval.SECONDS:
            count = int(self.time.timestamp()) + (self.years * 365_2422) // 10000
        elif interval == Interval.MONTHS:
            count = 12 * self._whole_years() + self.time.month
        elif interval == Interval.YEARS:
            count = self.time.year - YEAR_ZERO + self.years
        elif interval == Interval.MICROSECONDS:
            count = 10**6 * self._whole_seconds() + self.time.microsecond
        elif interval == Interval.YOCTOSECONDS:
            count = (
                self.yoctoseconds
                + self._whole_microseconds() * MICROSECOND_TO_YOCTOSECOND
            )
        else:
            raise ValueError(f"Logic error: {locals()=}")
        return Time(Interval(interval), time)

    def _from_years(self) -> int:
        return self.time.year - YEAR_ZERO + self.years

    def _from_microseconds(self) -> int:
        return 10**6 * self._from_seconds() + self.time.microsecond

    def _from_yoctoseconds(self) -> int:
        yoctoseconds = self._from_microseconds() * MICROSECOND_TO_YOCTOSECOND
        return yoctoseconds + self.yoctoseconds

    def _from_months(self) -> int:
        return 12 * self._from_years() + self.time.month
