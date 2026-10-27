"""Canonical truename conversion and explicit browsing over the category tree."""

from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel

from .category import Category, route
from .registry import ROOT
from .type_name import TypeNamer
from .types.tune import Tune
from .words import Words


class Result(BaseModel, frozen=True):
    type: str
    value: str
    truename: str
    vocabulary: str
    canonical: bool


class Nmr(Words):
    def __init__(
        self,
        words: Sequence[str] | Path | None = None,
        count: int | None = None,
        ignore_case: bool = True,
        root: Category = ROOT,
    ) -> None:
        super().__init__(words, count, ignore_case)
        self.root = root

    def types(self) -> dict[str, str]:
        return {p: c.description for p, _, c in self.root.leaves()}

    def encode(self, value: str, type_name: str, scope: str | None = None) -> Result:
        path, slots, codec = self.find_type(type_name)
        index = codec.str_to_index(value)
        canonical_value = codec.index_to_str(index)
        prefix = path if scope is None else scope.casefold().strip(":")
        _, prefix_slots = self.root.lookup("" if prefix == "name" else prefix)
        if slots[: len(prefix_slots)] != prefix_slots:
            raise ValueError("Prefix scope does not contain the selected type")
        truename = " ".join(self.to_truename(route(slots[len(prefix_slots) :], index)))
        if prefix:
            truename = short_prefix(self.root, prefix) + ":" + truename
        return Result(
            type=codec.label,
            value=canonical_value,
            truename=truename,
            vocabulary=self.identifier,
            canonical=True,
        )

    def decode(
        self, truename: str, browse: bool = False, vocabulary: str | None = None
    ) -> Result:
        if vocabulary is not None and vocabulary != self.identifier:
            raise ValueError("Vocabulary identifier does not match the selected list")
        truename, marked = unmark_truename(truename)
        prefix, separator, payload = truename.rpartition(":")
        if separator and not prefix:
            raise ValueError("A prefix cannot be empty")
        if not separator:
            payload = prefix or payload
            prefix = ""
        prefix = prefix.casefold()
        node, _ = self.root.lookup(prefix)
        index = self.from_truename(payload.split())
        codec: type[TypeNamer]
        if isinstance(node, Category):
            codec, value_index = node.resolve(index, browse)
        else:
            codec, value_index = node, index
        value = codec.index_to_str(value_index, browse)
        path = next(p for p, _, c in self.root.leaves() if c is codec)
        result = self.encode(value, path, prefix)
        normalized = " ".join(self.normalize(i) for i in payload.split())
        if prefix:
            normalized = short_prefix(self.root, prefix) + ":" + normalized
        canonical = result.truename == normalized
        if not browse and not canonical:
            raise ValueError(
                "Noncanonical truename; use browse explicitly to explore it"
            )
        return result.model_copy(
            update={
                "canonical": canonical,
                "truename": "name:" + result.truename if marked else result.truename,
            }
        )

    def find_type(self, type_name: str) -> tuple[str, list[int], type[TypeNamer]]:
        name = type_name.casefold().strip(":")
        node, slots = self.root.lookup(name)
        if isinstance(node, Category):
            raise ValueError(f"Unknown or ambiguous type: {type_name}")
        path = next(p for p, s, _ in self.root.leaves() if s == slots)
        return path, slots, node

    def to_tune(
        self, truename: str, absolute: bool = False, browse: bool = False
    ) -> Tune:
        """Interpret a canonical truename's payload or full root index as a tune."""
        result = self.decode(truename, browse)
        return Tune.from_index(self.truename_index(result.truename, absolute))

    def truename_index(self, truename: str, absolute: bool = True) -> int:
        """Read a truename's number without requiring an assigned object type."""
        truename, _ = unmark_truename(truename)
        prefix, separator, payload = truename.rpartition(":")
        if separator and not prefix:
            raise ValueError("A prefix cannot be empty")
        _, slots = self.root.lookup(prefix.casefold())
        index = self.from_truename(payload.split())
        if absolute:
            index = route(slots, index)
        return index


def unmark_truename(value: str) -> tuple[str, bool]:
    """Remove the category-free marker before interpreting a truename's index."""
    value = value.strip()
    prefix, separator, payload = value.partition(":")
    if separator and prefix.casefold() == "name":
        return payload.strip(), True
    return value, False


def short_prefix(root: Category, prefix: str) -> str:
    """Shorten a prefix only when it still selects the same routing scope."""
    prefix = prefix.removeprefix(":")
    short = prefix.rsplit(":", 1)[-1]
    if short in {"", "name"}:
        return short
    return short if root.lookup(short)[1] == root.lookup(prefix)[1] else prefix
