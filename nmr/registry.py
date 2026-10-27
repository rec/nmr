"""Explicit public allocations; importing a codec never modifies this tree."""

from .category import Category
from .types.chess import Chess
from .types.collections import List
from .types.floating import Float
from .types.fraction import Frac
from .types.go import Go
from .types.identifiers import Isbn, Upc
from .types.integer import Int
from .types.ip_address import IP
from .types.lat_long import LatLong
from .types.phone_number import Phone
from .types.sem_ver import Semver
from .types.string import String
from .types.temporal import Date, Duration, Time
from .types.tune import Tune
from .types.uuid import Uuid

ROOT = Category(
    "",
    Category("pure", Category("math", Int, Frac, Float)),
    Category(
        "real",
        Category("time", Date, Time, Duration),
        LatLong,
    ),
    Category(
        "data",
        Category("computer", IP, Uuid, Semver),
        Category("contact", Phone),
        Category("id", Isbn, Upc),
        String,
    ),
    Category("play", Category("game", Chess, Go), Category("music", Tune)),
    List,
)
