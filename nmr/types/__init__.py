from __future__ import annotations

from typing import Any

from ..categories import Category, make_category
from ..nameable_type import NameableType
from .fraction import Fraction
from .integer import Integer
from .ip_address import IPv4Address, IPv6Address
from .lat_long import LatLong
from .sem_ver import Semver
from .uuid import Uuid


def str_to_index(s: str) -> int:
    for cls in NameableType.SUBCLASSES.values():
        try:
            t = cls.str_to_type(s)  # type: ignore[attr-defined]
        except Exception:
            continue
        n: int = cls.type_to_index(t)  # type: ignore[attr-defined]
        return cls.category.number_to_index(n)

    raise ValueError(f"Cannot understand string '{s}'")


def index_to_str(index: int) -> str:
    category, n = make_category(index)
    cls = NameableType.SUBCLASSES[category.name]
    t = cls.index_to_type(n)
    return cls.type_to_str(t)


def names() -> list[str]:
    return [c.__class__.__name__.lower() for c in NameableType.SUBCLASSES.values()]


def get_class(prefix: str) -> type[NameableType[Any]]:
    cl = [
        c
        for c in NameableType.SUBCLASSES.values()
        if c.__class__.__name__.lower().startswith(prefix.lower())
    ]
    if not cl:
        raise ValueError(f"Unknown {prefix=}")
    if len(cl) > 1:
        raise ValueError(f"Ambiguous {prefix=}, could be {cl}")
    return cl[0]
