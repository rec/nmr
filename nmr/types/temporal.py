"""Gregorian date/time codecs with exact microsecond arithmetic, independent of TZ."""

import re
from datetime import date, time

from ..type_name import TypeNamer
from .bounded import bounded


class Date(TypeNamer):
    label = "date"
    description = "Gregorian date YYYY-MM-DD, years 0001 through 9999"

    @staticmethod
    def str_to_index(value: str) -> int:
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
            raise ValueError("Use an unambiguous YYYY-MM-DD date")
        return date.fromisoformat(value).toordinal() - 1

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        return date.fromordinal(1 + bounded(index, DAYS, browse)).isoformat()


class Time(TypeNamer):
    label = "time"
    description = "Time of day HH:MM[:SS[.ffffff]], without a timezone"

    @staticmethod
    def str_to_index(value: str) -> int:
        if not re.fullmatch(TIME, value):
            raise ValueError(
                "Use HH:MM[:SS[.ffffff]], with at most six fractional digits"
            )
        result = time.fromisoformat(value)
        return (
            (result.hour * 60 + result.minute) * 60 + result.second
        ) * SECOND + result.microsecond

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        index = bounded(index, DAY, browse)
        seconds, micros = divmod(index, SECOND)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return time(hours, minutes, seconds, micros).isoformat()


class DateTime(TypeNamer):
    label = "datetime"
    description = (
        "Gregorian date and time YYYY-MM-DDTHH:MM[:SS[.ffffff]], without a timezone"
    )

    @staticmethod
    def str_to_index(value: str) -> int:
        if not (match := re.fullmatch(r"([0-9]{4}-[0-9]{2}-[0-9]{2})[T ](.+)", value)):
            raise ValueError("Use YYYY-MM-DDTHH:MM[:SS[.ffffff]], without a timezone")
        return Date.str_to_index(match[1]) * DAY + Time.str_to_index(match[2])

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        day, clock = divmod(bounded(index, DAYS * DAY, browse), DAY)
        return Date.index_to_str(day) + "T" + Time.index_to_str(clock)


TIME = r"(?:[01][0-9]|2[0-3]):[0-5][0-9](?::[0-5][0-9](?:\.[0-9]{1,6})?)?"
SECOND = 10**6
DAY = 86400 * SECOND
DAYS = date.max.toordinal()
