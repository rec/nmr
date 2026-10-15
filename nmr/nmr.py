"""Canonical naming and explicit browsing over the category tree."""

from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel

from .category import Category, route
from .registry import ROOT
from .type_namer import TypeNamer
from .words import Words


class Result(BaseModel, frozen=True):
    type: str
    value: str
    name: str
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
        _, prefix_slots = self.root.lookup(prefix)
        if slots[: len(prefix_slots)] != prefix_slots:
            raise ValueError("Prefix scope does not contain the selected type")
        name = " ".join(self.encode_to_name(route(slots[len(prefix_slots) :], index)))
        if prefix:
            name = prefix + ":" + name
        return Result(
            type=path,
            value=canonical_value,
            name=name,
            vocabulary=self.identifier,
            canonical=True,
        )

    def decode(
        self, name: str, browse: bool = False, vocabulary: str | None = None
    ) -> Result:
        if vocabulary is not None and vocabulary != self.identifier:
            raise ValueError("Vocabulary identifier does not match the selected list")
        prefix, separator, payload = name.strip().rpartition(":")
        if separator and not prefix:
            raise ValueError("A prefix cannot be empty")
        if not separator:
            payload = prefix or payload
            prefix = ""
        prefix = prefix.casefold()
        node, _ = self.root.lookup(prefix)
        index = self.decode_from_name(payload.split())
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
            normalized = prefix + ":" + normalized
        canonical = result.name == normalized
        if not browse and not canonical:
            raise ValueError("Noncanonical name; use browse explicitly to explore it")
        return result.model_copy(update={"canonical": canonical})

    def find_type(self, type_name: str) -> tuple[str, list[int], type[TypeNamer]]:
        name = type_name.casefold().strip(":")
        matches = [
            (p, s, c) for p, s, c in self.root.leaves() if p == name or c.label == name
        ]
        if len(matches) != 1:
            raise ValueError(f"Unknown or ambiguous type: {type_name}")
        return matches[0]
