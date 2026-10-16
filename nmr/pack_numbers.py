"""Exact sum-layer enumeration of fixed-length nonnegative integer tuples."""

from itertools import pairwise
from math import comb, isqrt

from pydantic import BaseModel, Field


class Packer(BaseModel, frozen=True):
    count: int = Field(ge=1)

    def pack(self, *numbers: int) -> int:
        if len(numbers) != self.count or any(i < 0 for i in numbers):
            raise ValueError(f"Expected {self.count} nonnegative integers")
        total = 0
        tail = 0
        for size, value in enumerate(reversed(numbers), 1):
            tail += value
            total += comb(tail + size - 1, size)
        return total

    def unpack(self, n: int) -> list[int]:
        if n < 0:
            raise ValueError("Expected a nonnegative integer")
        if self.count == 1:
            return [n]
        sums = []
        # comb(b, k) >= (b/k)**k gives an integer-only initial upper bound.
        upper = self.count * (1 << ((n.bit_length() + self.count - 1) // self.count))
        for size in range(self.count, 2, -1):
            lower = size - 1
            while upper - lower > 1:
                middle = (lower + upper) // 2
                if comb(middle, size) <= n:
                    lower = middle
                else:
                    upper = middle
            sums.append(lower - size + 1)
            n -= comb(lower, size)
            # The next binomial's upper argument must be smaller than this one.
            upper = lower
        first, last = unpair(n)
        sums.extend([first + last, last, 0])
        return [i - j for i, j in pairwise(sums)]


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


def rank_digits(digits: list[int], base: int) -> int:
    total = 0
    for digit in digits:
        total = base * total + digit + 1
    return total


def unrank_digits(index: int, base: int) -> list[int]:
    if index < 0:
        raise ValueError("Expected a nonnegative index")
    digits = []
    while index:
        index, digit = divmod(index - 1, base)
        digits.append(digit)
    return digits[::-1]
