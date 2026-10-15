"""Exact bijections between nonnegative integer tuples and integers."""

from math import isqrt

from pydantic import BaseModel, Field


class Packer(BaseModel, frozen=True):
    count: int = Field(ge=1)
    forward: bool = True

    def pack(self, *numbers: int) -> int:
        if len(numbers) != self.count or any(i < 0 for i in numbers):
            raise ValueError(f"Expected {self.count} nonnegative integers")
        values = list(numbers)
        if self.forward:
            total = values.pop()
            for i in reversed(values):
                total = pair(i, total)
        else:
            total = values.pop(0)
            for i in values:
                total = pair(total, i)
        return total

    def unpack(self, n: int) -> list[int]:
        if n < 0:
            raise ValueError("Expected a nonnegative integer")
        values = []
        for _ in range(self.count - 1):
            if self.forward:
                first, n = unpair(n)
                values.append(first)
            else:
                n, last = unpair(n)
                values.append(last)
        return values + [n] if self.forward else [n] + values[::-1]


def pair(x: int, y: int) -> int:
    if x < 0 or y < 0:
        raise ValueError("Expected nonnegative integers")
    return (x + y) * (x + y + 1) // 2 + y


def unpair(n: int) -> tuple[int, int]:
    if n < 0:
        raise ValueError("Expected a nonnegative integer")
    diagonal = (isqrt(8 * n + 1) - 1) // 2
    y = n - diagonal * (diagonal + 1) // 2
    return diagonal - y, y
