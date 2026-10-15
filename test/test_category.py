import pytest

from nmr.category import Category, route
from nmr.registry import ROOT
from nmr.types.floating import Float
from nmr.types.integer import Int


def test_last_slot_never_accepts_a_leaf() -> None:
    with pytest.raises(ValueError, match="last slot"):
        Category(name="bad", children={4: Int})


def test_growth_preserves_old_allocations() -> None:
    old = Category(name="root", children={0: Int})
    new = Category(
        name="root", children={0: Int, 4: Category(name="extra", children={0: Int})}
    )
    for i in range(100):
        assert old.resolve(route([0], i)) == new.resolve(route([0], i)) == (Int, i)
        assert new.resolve(route([4, 0], i)) == (Int, i)


def test_root_order_and_reserved_slot() -> None:
    assert [i.name for i in ROOT.children.values() if isinstance(i, Category)] == [
        "universal",
        "physical",
        "virtual",
        "play",
        "meta",
    ]
    with pytest.raises(ValueError, match="unassigned"):
        ROOT.resolve(route([0, 3], 0))
    assert ROOT.resolve(route([0, 3], 0), browse=True)[0] is Int


def test_browsing_empty_categories_uses_slot_order() -> None:
    empty = Category(name="empty", children={})
    first = Category(name="root", children={0: Int, 1: empty, 2: Float})
    second = Category(name="root", children={2: Float, 1: empty, 0: Int})
    assert first.resolve(1, browse=True) == second.resolve(1, browse=True) == (Float, 0)
