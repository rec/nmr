"""Five-way routing. Slot four is always empty or a category."""

from __future__ import annotations

from collections.abc import Iterator

from pydantic import BaseModel, ConfigDict, model_validator

from .type_namer import TypeNamer

RADIX = 5


class Category(BaseModel, frozen=True):
    name: str
    children: dict[int, Category | type[TypeNamer]]

    @model_validator(mode="after")
    def validate_children(self) -> Category:
        if any(i < 0 or i >= RADIX for i in self.children):
            raise ValueError("Category slots must be between 0 and 4")
        if 4 in self.children and not isinstance(self.children[4], Category):
            raise ValueError("The last slot can never be a leaf")
        labels = [label(i) for i in self.children.values()]
        if len(labels) != len(set(labels)):
            raise ValueError("Sibling names must be unique")
        return self

    def leaves(
        self, prefix: str = ""
    ) -> Iterator[tuple[str, list[int], type[TypeNamer]]]:
        for slot, child in sorted(self.children.items()):
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
            matches = [(s, c) for s, c in node.children.items() if label(c) == part]
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
            if slot not in node.children:
                if not browse:
                    raise ValueError("Name selects an unassigned category slot")
                available = [
                    s
                    for s, c in sorted(node.children.items())
                    if not isinstance(c, Category) or list(c.leaves())
                ]
                if not available:
                    raise ValueError("No implemented types in this category")
                slot = available[slot % len(available)]
            child = node.children[slot]
            if browse and isinstance(child, Category) and not list(child.leaves()):
                available = [
                    c
                    for c in node.children.values()
                    if not isinstance(c, Category) or list(c.leaves())
                ]
                if not available:
                    raise ValueError("No implemented types in this category")
                child = available[slot % len(available)]
            node = child
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
