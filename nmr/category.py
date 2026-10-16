"""Five-way routing. Only the unnamed root may have a leaf in slot four."""

from __future__ import annotations

from collections.abc import Iterator

from pydantic import BaseModel, ConfigDict, model_validator

from .type_namer import TypeNamer

RADIX = 5


class Category(BaseModel, frozen=True):
    name: str
    children: tuple[Category | type[TypeNamer], ...]

    def __init__(self, name: str, *children: Category | type[TypeNamer]) -> None:
        super().__init__(name=name, children=children)

    @model_validator(mode="after")
    def validate_children(self) -> Category:
        if not 1 <= len(self.children) <= RADIX:
            raise ValueError(f"Child count {len(self.children)} is out of range 1..5")
        if (
            self.name
            and len(self.children) == RADIX
            and not isinstance(self.children[-1], Category)
        ):
            raise ValueError("The last slot can never be a leaf")
        if any(isinstance(i, Category) and not i.name for i in self.children):
            raise ValueError("The unnamed root cannot be nested inside a category")
        labels = [label(i) for i in self.children]
        if len(labels) != len(set(labels)):
            raise ValueError("Sibling names must be unique")
        return self

    def leaves(
        self, prefix: str = ""
    ) -> Iterator[tuple[str, list[int], type[TypeNamer]]]:
        for slot, child in enumerate(self.children):
            path = f"{prefix}{label(child)}"
            if isinstance(child, Category):
                for name, slots, codec in child.leaves(path + ":"):
                    yield name, [slot, *slots], codec
            else:
                yield path, [slot], child

    def lookup(self, path: str) -> tuple[Category | type[TypeNamer], list[int]]:
        node: Category | type[TypeNamer] = self
        slots: list[int] = []
        if not path:
            return node, slots
        for part in path.split(":"):
            if not isinstance(node, Category):
                raise ValueError(f"Extra components after a leaf: {path}")
            matches = [(s, c) for s, c in enumerate(node.children) if label(c) == part]
            if not matches:
                raise ValueError(f"Unknown category or type: {path}")
            slot, node = matches[0]
            slots.append(slot)
        return node, slots

    def resolve(self, index: int, browse: bool = False) -> tuple[type[TypeNamer], int]:
        if index < 0:
            raise ValueError("Expected a nonnegative index")
        node: Category | type[TypeNamer] = self
        while isinstance(node, Category):
            index, slot = divmod(index, RADIX)
            if slot >= len(node.children):
                if not browse:
                    raise ValueError("Name selects an unassigned category slot")
                slot %= len(node.children)
            node = node.children[slot]
        return node, index

    model_config = ConfigDict(arbitrary_types_allowed=True)


def label(node: Category | type[TypeNamer]) -> str:
    return node.name if isinstance(node, Category) else node.label


def route(slots: list[int], index: int) -> int:
    if index < 0:
        raise ValueError("Expected a nonnegative index")
    for slot in reversed(slots):
        index = slot + RADIX * index
    return index
