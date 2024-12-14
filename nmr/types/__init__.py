from __future__ import annotations

from ..nameable_type import NameableType
from .fraction import Fraction
from .hex import Hex
from .integer import Integer
from .ip_address import IpAddress
from .lat_long import LatLong
from .sem_ver import Semver
from .uuid import Uuid

CLASSES = Hex, Fraction, Integer, IpAddress, LatLong, Semver, Uuid
NAMES = tuple(c.__name__.lower() for c in CLASSES)


def try_to_int(s: str) -> int | str:
    ci = class_int(s)
    return s if ci is None else ci[1]


def class_int(s: str) -> tuple[type, int] | None:
    for c in CLASSES:
        i = c.to_int(s)
        if i is not None:
            return c, i
    return None


def get_class(prefix: str) -> type[NameableType]:
    cl = [c for (n, c) in zip(NAMES, CLASSES) if n.startswith(prefix)]
    if not cl:
        raise ValueError(f"Unknown {prefix=}")
    if len(cl) > 1:
        raise ValueError(f"Ambiguous {prefix=}, could be {cl}")
    return cl[0]
