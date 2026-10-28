"""Gregorian date/time codecs, centered on zoot by default, independent of TZ."""

import re
from datetime import date, time

from ..type_name import TypeNamer
from .bounded import bounded
from .integer import signed_index, signed_value


class Date(TypeNamer):
    label = "date"
    description = "Gregorian date YYYY-MM-DD, years 0001 through 9999"

    @staticmethod
    def str_to_index(value: str, *, center_on_zoot: bool = True) -> int:
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
            raise ValueError("Use an unambiguous YYYY-MM-DD date")
        index = date.fromisoformat(value).toordinal() - 1
        return signed_index(index - ZOOT) if center_on_zoot else index

    @staticmethod
    def index_to_str(
        index: int, browse: bool = False, *, center_on_zoot: bool = True
    ) -> str:
        if center_on_zoot:
            index = signed_value(index) + ZOOT
            if browse:
                index %= DAYS
        return date.fromordinal(1 + bounded(index, DAYS, browse)).isoformat()


class Time(TypeNamer):
    label = "time"
    description = "Time of day HH:MM[:SS], without a timezone"

    @staticmethod
    def str_to_index(value: str) -> int:
        if not re.fullmatch(TIME, value):
            raise ValueError("Use HH:MM[:SS], without fractional seconds")
        result = time.fromisoformat(value)
        return (result.hour * 60 + result.minute) * 60 + result.second

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        index = bounded(index, DAY, browse)
        hours, seconds = divmod(index, 3600)
        minutes, seconds = divmod(seconds, 60)
        return time(hours, minutes, seconds).isoformat()


class DateTime(TypeNamer):
    label = "datetime"
    description = "Gregorian date and time YYYY-MM-DDTHH:MM[:SS], without a timezone"

    @staticmethod
    def str_to_index(value: str, *, center_on_zoot: bool = True) -> int:
        if not (match := re.fullmatch(r"([0-9]{4}-[0-9]{2}-[0-9]{2})[T ](.+)", value)):
            raise ValueError("Use YYYY-MM-DDTHH:MM[:SS], without a timezone")
        day = Date.str_to_index(match[1], center_on_zoot=False)
        index = day * DAY + Time.str_to_index(match[2])
        return signed_index(index - ZOOT * DAY) if center_on_zoot else index

    @staticmethod
    def index_to_str(
        index: int, browse: bool = False, *, center_on_zoot: bool = True
    ) -> str:
        if center_on_zoot:
            index = signed_value(index) + ZOOT * DAY
            if browse:
                index %= DAYS * DAY
        day, clock = divmod(bounded(index, DAYS * DAY, browse), DAY)
        return (
            Date.index_to_str(day, center_on_zoot=False)
            + "T"
            + Time.index_to_str(clock)
        )


TIME = r"(?:[01][0-9]|2[0-3]):[0-5][0-9](?::[0-5][0-9])?"
DAY = 86400
DAYS = date.max.toordinal()
ZOOT = date(2027, 1, 1).toordinal() - 1
