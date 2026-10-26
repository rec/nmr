"""Published format fixtures must survive every compatible extension."""

import json
from pathlib import Path
from typing import ClassVar

import pytest

from nmr.category import Category
from nmr.nmr import Nmr
from nmr.registry import ROOT
from nmr.types.integer import Int


class Added(Int):
    label: ClassVar[str] = "added"


def test_published_format_fixtures() -> None:
    fixture = json.loads(Path(__file__).with_name("format.json").read_text())
    engine = Nmr()
    assert engine.identifier == fixture["vocabulary"]
    for case in fixture["cases"]:
        result = engine.encode(case["input"], case["type"], case["scope"])
        assert result.truename == case["truename"]
        assert result.truename.count(":") <= 1
        assert ":" not in result.type
        assert result.value == case["value"]
        assert engine.decode(case["truename"]).value == case["value"]


def test_new_categories_preserve_every_established_fixture() -> None:
    pure = ROOT.children[0]
    assert isinstance(pure, Category)
    extra = Category("extra", Added)
    expanded_pure = Category("pure", *pure.children, extra)
    expanded = Category("", expanded_pure, *ROOT.children[1:])
    engine = Nmr(root=expanded)
    fixture = json.loads(Path(__file__).with_name("format.json").read_text())
    for case in fixture["cases"]:
        assert engine.decode(case["truename"]).value == case["value"]
        assert (
            engine.encode(case["input"], case["type"], case["scope"]).truename
            == case["truename"]
        )
    new_truename = engine.encode("42", "added", scope="").truename
    assert engine.decode(new_truename).value == "42"
    with pytest.raises(ValueError, match="unassigned"):
        Nmr().decode(new_truename)
