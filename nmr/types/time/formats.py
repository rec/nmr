from __future__ import annotations

import itertools
from datetime import datetime
from functools import partial
from typing import Callable, Iterable, Sequence

from .constants import Interval
from .time import Time


def from_string(s: str) -> Time:
    def parse(p: str) -> datetime | None:
        try:
            return datetime.strptime(s, p)
        except ValueError:
            return None

    all_parsers = ((i, p) for i, parsers in PARSERS.items() for p in parsers)
    times = [Time(i, dt) for i, p in all_parsers if (dt := parse(p))]
    if not times:
        raise ValueError("No format matched")
    if len(times) > 1:
        raise ValueError(f"Multiple formats matched {times=}")
    return times[0]


def to_string(t: Time) -> str:
    return t.time.strftime(PARSERS[t.interval][0])


def _product(*patterns: str, sep: str = " /") -> Iterable[str]:
    yield from ("%" + f"{sep}%".join(c) for s, c in itertools.product(sep, *patterns))


PARSERS: dict[Interval, Sequence[str]] = {
    Interval.SECOND: ["%H:%M:%S", "%I:%M:%S%p"],
    Interval.MINUTE: ["%H:%M", "%Hh%M", "%I:%M%p"],
    Interval.HOUR: ["%Hh", "%I%p"],
    Interval.DAY: [
        *_product("d", "bBm", "Yy"),
        *_product("Yy", "bBm", "d"),
        *_product("d", "bBm"),
        *_product("bBm", "d"),
    ],
    # Interval.WEEK: ["%m/%y"],
    Interval.MONTH: [
        *_product("bBm", "Yy"),
        *_product("Yy", "bBm"),
        *_product("bBm"),
        *_product("d"),
    ],
    Interval.YEAR: [*_product("Yy")],
    # Interval.DECADE: [_decade],
    # Interval.CENTURY: [_century],
}
