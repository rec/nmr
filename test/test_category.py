import pytest

from nmr.category import Category, label, route
from nmr.registry import ROOT
from nmr.types.collections import List
from nmr.types.floating import Float
from nmr.types.fraction import Frac
from nmr.types.integer import Int
from nmr.types.uuid import Uuid


def test_named_categories_reject_last_slot_leaves() -> None:
    with pytest.raises(ValueError, match="last slot"):
        Category("bad", Int, Float, Frac, Uuid, Int)


def test_growth_preserves_old_allocations() -> None:
    old = Category("root", Int, Float, Frac, Uuid)
    new = Category("root", *old.children, Category("extra", Int))
    for i in range(100):
        assert old.resolve(route([0], i)) == new.resolve(route([0], i)) == (Int, i)
        assert new.resolve(route([4, 0], i)) == (Int, i)


def test_root_order_and_unassigned_slots() -> None:
    assert [label(i) for i in ROOT.children] == [
        "pure",
        "real",
        "data",
        "play",
        "list",
    ]
    with pytest.raises(ValueError, match="unassigned"):
        ROOT.resolve(route([0, 3], 0))
    assert ROOT.resolve(route([0, 3], 0), browse=True)[0] is Int


def test_only_the_root_can_have_a_leaf_in_the_last_slot() -> None:
    assert ROOT.resolve(route([4], 123)) == (List, 123)
    with pytest.raises(ValueError, match="last slot"):
        Category("nested", *ROOT.children)
    with pytest.raises(ValueError, match="cannot be nested"):
        Category("nested", ROOT)


def test_browsing_unassigned_slots_uses_child_order() -> None:
    category = Category("root", Int, Float)
    assert category.resolve(3, browse=True) == (Float, 0)


def test_categories_store_immutable_ordered_children() -> None:
    category = Category("root", Int, Category("nested", Float))
    assert isinstance(category.children, tuple)
    assert list(category.leaves()) == [
        ("int", [0], Int),
        ("nested:float", [1, 0], Float),
    ]
    with pytest.raises(ValueError, match="frozen"):
        category.children = (Float,)


def test_categories_reject_invalid_children() -> None:
    with pytest.raises(ValueError, match="out of range"):
        Category("empty")
    with pytest.raises(ValueError, match="out of range"):
        Category("too many", Int, Int, Int, Int, Int, Int)
    with pytest.raises(ValueError):
        Category("null", None)
    with pytest.raises(ValueError):
        Category("unrelated", str)
    with pytest.raises(ValueError, match="unique"):
        Category("duplicate", Int, Int)
