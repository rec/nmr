import pytest

from nmr.category import Category, label, route
from nmr.nmr import Nmr
from nmr.registry import ROOT
from nmr.types.collections import List
from nmr.types.floating import Float
from nmr.types.fraction import Frac
from nmr.types.integer import Int
from nmr.types.temporal import Time
from nmr.types.uuid import Uuid


def test_category_and_type_names_are_unique_except_the_time_category_and_type() -> None:
    nodes = [(p, label(n).casefold()) for p, _, n in ROOT.nodes()]
    duplicates = {
        n: [p for p, k in nodes if k == n]
        for _, n in nodes
        if sum(k == n for _, k in nodes) > 1
    }
    assert duplicates == {"time": ["real:time", "real:time:time"]}


@pytest.mark.parametrize(
    "path", ["chess", "game:chess", "play:game:chess", ":play:game:chess"]
)
def test_lookup_accepts_omitted_parent_categories(path: str) -> None:
    assert ROOT.lookup(path) == ROOT.lookup("play:game:chess")


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


def test_bare_time_selects_the_leaf_and_real_time_selects_the_category() -> None:
    assert ROOT.lookup("time") == (Time, [1, 0, 1])
    node, slots = ROOT.lookup("real:time")
    assert isinstance(node, Category)
    assert slots == [1, 0]


@pytest.mark.parametrize(
    "type_name,path",
    [
        ("ip", "data:address:ip"),
        ("phone", "data:address:phone"),
        ("isbn", "data:register:isbn"),
        ("upc", "data:register:upc"),
        ("uuid", "data:id:uuid"),
        ("semver", "data:id:semver"),
    ],
)
def test_data_types_use_their_requested_categories(type_name: str, path: str) -> None:
    assert Nmr().find_type(type_name)[0] == path


@pytest.mark.parametrize("category", ["computer", "contact"])
def test_removed_data_categories_are_not_available(category: str) -> None:
    with pytest.raises(ValueError, match="Unknown"):
        ROOT.lookup(category)
