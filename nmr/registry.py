"""Explicit public allocations; importing a codec never modifies this tree."""

from .category import Category
from .types.floating import Float
from .types.fraction import Frac
from .types.integer import Int

ROOT = Category(
    name="",
    children={
        0: Category(
            name="universal",
            children={
                0: Category(name="math", children={0: Int, 1: Frac, 2: Float}),
            },
        ),
        1: Category(name="physical", children={}),
        2: Category(name="virtual", children={}),
        3: Category(name="play", children={}),
        4: Category(name="meta", children={}),
    },
)
