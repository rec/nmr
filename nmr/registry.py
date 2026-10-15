"""Explicit public allocations; importing a codec never modifies this tree."""

from .category import Category
from .types.chess import Chess
from .types.collections import List, Record
from .types.floating import Float
from .types.fraction import Frac
from .types.go import Go
from .types.identifiers import Isbn, Upc
from .types.integer import Int
from .types.ip_address import IPv4, IPv6
from .types.lat_long import LatLong
from .types.phone_number import Phone
from .types.sem_ver import Semver
from .types.temporal import Clock, Date, Duration, Instant, Local
from .types.text import Text
from .types.uuid import Uuid

ROOT = Category(
    name="",
    children={
        0: Category(
            name="universal",
            children={
                0: Category(name="math", children={0: Int, 1: Frac, 2: Float}),
            },
        ),
        1: Category(
            name="physical",
            children={
                0: Category(
                    name="time", children={0: Date, 1: Clock, 2: Local, 3: Instant}
                ),
                1: LatLong,
                2: Duration,
            },
        ),
        2: Category(
            name="virtual",
            children={
                0: Category(
                    name="computer", children={0: IPv4, 1: IPv6, 2: Uuid, 3: Semver}
                ),
                1: Category(name="contact", children={0: Phone}),
                2: Category(name="id", children={0: Isbn, 1: Upc}),
                3: Text,
            },
        ),
        3: Category(
            name="play",
            children={
                0: Category(name="game", children={0: Chess, 1: Go}),
            },
        ),
        4: Category(name="meta", children={0: List, 1: Record}),
    },
)
