"""Deck permutations, ordered by displaced-card count, then subset and image order."""

import re
from functools import cache
from math import comb, factorial

from ..type_name import TypeNamer
from .bounded import bounded


class Cards(TypeNamer):
    label = "cards"
    description = "52-card deck: changed-position cycles such as (1 2); () is ordered"

    @staticmethod
    def str_to_index(value: str) -> int:
        value = value.strip()
        permutation = list(range(DECK_SIZE))
        if re.fullmatch(r"\(\s*\)", value):
            return 0
        cycles = re.findall(r"\(([^()]*)\)", value)
        if not cycles or re.sub(r"\([^()]*\)", "", value).strip():
            raise ValueError("Use () or changed-position cycles such as (1 2)")
        used: set[int] = set()
        for cycle in cycles:
            tokens = cycle.split()
            if len(tokens) < 2 or any(not re.fullmatch(r"[0-9]+", i) for i in tokens):
                raise ValueError("Each cycle needs at least two numbered positions")
            positions = [int(i) - 1 for i in tokens]
            for position in positions:
                if not 0 <= position < DECK_SIZE or position in used:
                    raise ValueError("Positions must be distinct numbers from 1 to 52")
                used.add(position)
            for origin, destination in zip(
                positions, positions[1:] + positions[:1], strict=True
            ):
                permutation[origin] = destination
        return rank_permutation(permutation)

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        permutation = unrank_permutation(bounded(index, DECK_COUNT, browse), DECK_SIZE)
        cycles = []
        used: set[int] = set()
        for origin, destination in enumerate(permutation):
            if origin == destination or origin in used:
                continue
            cycle = []
            position = origin
            while position not in used:
                used.add(position)
                cycle.append(position + 1)
                position = permutation[position]
            cycles.append("(" + " ".join(str(i) for i in cycle) + ")")
        return " ".join(cycles) or "()"


def rank_permutation(permutation: list[int]) -> int:
    """Rank by displaced count, lexicographic displaced subset, then images."""
    size = len(permutation)
    if sorted(permutation) != list(range(size)):
        raise ValueError("Expected a permutation of 0 through size minus one")
    positions = [i for i, n in enumerate(permutation) if i != n]
    moved = len(positions)
    offset = sum(comb(size, i) * completions(i, i) for i in range(moved))
    subset_rank = 0
    previous = -1
    for i, position in enumerate(positions):
        for candidate in range(previous + 1, position):
            subset_rank += comb(size - candidate - 1, moved - i - 1)
        previous = position
    remaining = set(positions)
    future = set(positions)
    forbidden = moved
    arrangement_rank = 0
    for position in positions:
        future.remove(position)
        for card in sorted(remaining):
            if card == position:
                continue
            next_forbidden = forbidden - (position in remaining) - (card in future)
            if card == permutation[position]:
                remaining.remove(card)
                forbidden = next_forbidden
                break
            arrangement_rank += completions(len(remaining) - 1, next_forbidden)
    return offset + subset_rank * completions(moved, moved) + arrangement_rank


def unrank_permutation(index: int, size: int) -> list[int]:
    """Invert rank_permutation by skipping counted subsets and image prefixes."""
    index = bounded(index, factorial(size), False)
    moved = 0
    while index >= (count := comb(size, moved) * completions(moved, moved)):
        index -= count
        moved += 1
    subset_rank, arrangement_rank = divmod(index, completions(moved, moved))
    positions = []
    candidate = 0
    for remaining_positions in range(moved, 0, -1):
        for position in range(candidate, size):
            count = comb(size - position - 1, remaining_positions - 1)
            if subset_rank >= count:
                subset_rank -= count
            else:
                positions.append(position)
                candidate = position + 1
                break
    permutation = list(range(size))
    remaining = set(positions)
    future = set(positions)
    forbidden = moved
    for position in positions:
        future.remove(position)
        for card in sorted(remaining):
            if card == position:
                continue
            next_forbidden = forbidden - (position in remaining) - (card in future)
            count = completions(len(remaining) - 1, next_forbidden)
            if arrangement_rank >= count:
                arrangement_rank -= count
            else:
                permutation[position] = card
                remaining.remove(card)
                forbidden = next_forbidden
                break
    return permutation


@cache
def completions(size: int, forbidden: int) -> int:
    """Count bijections with disjoint forbidden position/card matches remaining."""
    if forbidden == 0:
        return factorial(size)
    return completions(size, forbidden - 1) - completions(size - 1, forbidden - 1)


DECK_SIZE = 52
DECK_COUNT = factorial(DECK_SIZE)
