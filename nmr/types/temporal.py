"""Gregorian date/time codecs with exact microsecond arithmetic, independent of TZ."""

import re
from datetime import date, time

from ..type_truenamer import TypeTruenamer
from .bounded import bounded, scaled_integer, scaled_string
from .integer import signed_index, signed_value


class Date(TypeTruenamer):
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


class Clock(TypeTruenamer):
    label = "clock"
    description = "Time of day HH:MM[:SS[.ffffff]], without a timezone"

    @staticmethod
    def str_to_index(value: str) -> int:
        if not re.fullmatch(CLOCK, value):
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


class Duration(TypeTruenamer):
    label = "duration"
    description = (
        "Signed elapsed decimal seconds, with optional s suffix; microsecond precision"
    )

    @staticmethod
    def str_to_index(value: str) -> int:
        return signed_index(scaled_integer(value.removesuffix("s"), SECOND))

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        return scaled_string(signed_value(index), SECOND) + "s"


CLOCK = r"(?:[01][0-9]|2[0-3]):[0-5][0-9](?::[0-5][0-9](?:\.[0-9]{1,6})?)?"
SECOND = 10**6
DAY = 86400 * SECOND
DAYS = date.max.toordinal()
