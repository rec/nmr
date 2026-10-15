"""Gregorian date/time codecs with exact microsecond arithmetic, independent of TZ."""

import re
from datetime import date, datetime, time, timezone

from ..type_namer import TypeNamer
from .bounded import bounded, scaled_integer, scaled_string
from .integer import signed_index, signed_value


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


class Clock(TypeNamer):
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


class Local(TypeNamer):
    label = "local"
    description = "Local date and time YYYY-MM-DDTHH:MM:SS[.ffffff], no timezone"

    @staticmethod
    def str_to_index(value: str) -> int:
        parts = value.split("T")
        if len(parts) != 2:
            raise ValueError("Use YYYY-MM-DDTHH:MM:SS[.ffffff]")
        return Date.str_to_index(parts[0]) * DAY + Clock.str_to_index(parts[1])

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        day, clock = divmod(bounded(index, DAYS * DAY, browse), DAY)
        return Date.index_to_str(day) + "T" + Clock.index_to_str(clock)


class Instant(TypeNamer):
    label = "instant"
    description = "Offset-aware timestamp, normalized to UTC; years 0001 through 9999"

    @staticmethod
    def str_to_index(value: str) -> int:
        if not re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}T"
            + CLOCK
            + r"(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])",
            value,
        ):
            raise ValueError("Timestamp needs an explicit Z or ±HH:MM offset")
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        try:
            timestamp = timestamp.astimezone(timezone.utc)
        except OverflowError as error:
            raise ValueError("UTC timestamp outside years 0001 through 9999") from error
        return Local.str_to_index(timestamp.replace(tzinfo=None).isoformat())

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        return Local.index_to_str(index, browse) + "Z"


class Duration(TypeNamer):
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


CLOCK = r"[0-9]{2}:[0-9]{2}(?::[0-9]{2}(?:\.[0-9]{1,6})?)?"
SECOND = 10**6
DAY = 86400 * SECOND
DAYS = date.max.toordinal()
