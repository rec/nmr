"""Unicode strings ranked by total character cost, with common letters first."""

from bisect import bisect_right
from functools import lru_cache
from string import ascii_lowercase, ascii_uppercase

from ..type_name import TypeNamer
from .bounded import bounded


class String(TypeNamer):
    label = "string"
    description = "Unicode text excluding C0/C1 controls, DELETE, and surrogates"

    @staticmethod
    def str_to_index(value: str) -> int:
        digits = [character_index(i) for i in value]
        remaining = sum((1 + i // len(LETTERS)).bit_length() for i in digits)
        counts, starts = string_counts(remaining)
        index = starts[remaining]
        for digit in digits:
            for weight, (lower, upper) in enumerate(CHARACTER_GROUPS, 1):
                if weight > remaining:
                    break
                index += max(0, min(digit, upper) - lower) * counts[remaining - weight]
            remaining -= (1 + digit // len(LETTERS)).bit_length()
        return index

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        if index < 0:
            raise ValueError("Expected a nonnegative string index")
        # The 52 cost-one letters alone provide at least 32**cost strings.
        counts, starts = string_counts((index.bit_length() + 4) // 5)
        remaining = bisect_right(starts, index) - 1
        rank = index - starts[remaining]
        result = []
        while remaining:
            for weight, (lower, upper) in enumerate(CHARACTER_GROUPS, 1):
                if weight > remaining:
                    break
                completions = counts[remaining - weight]
                block = (upper - lower) * completions
                if rank >= block:
                    rank -= block
                    continue
                offset, rank = divmod(rank, completions)
                result.append(character_from_index(lower + offset))
                remaining -= weight
                break
            else:
                raise AssertionError("String completion count is inconsistent")
        return "".join(result)


@lru_cache(maxsize=1)
def string_counts(limit: int) -> tuple[list[int], list[int]]:
    """Count exact-cost strings and strictly preceding layers, including empty."""
    counts = [1]
    starts = [0, 1]
    for cost in range(1, limit + 1):
        counts.append(
            sum(
                (b - a) * counts[cost - w]
                for w, (a, b) in enumerate(CHARACTER_GROUPS, 1)
                if w <= cost
            )
        )
        starts.append(starts[-1] + counts[-1])
    return counts, starts


def character_index(character: str) -> int:
    code = ord(character)
    if code < 0x20 or 0x7F <= code < 0xA0 or 0xD800 <= code < 0xE000:
        raise ValueError("String excludes C0/C1 controls, DELETE, and surrogates")
    if code < 0x100:
        return LOW_CHARACTERS.index(character)
    return code - 0x100 + len(LOW_CHARACTERS) - (0x800 if code >= 0xE000 else 0)


def character_from_index(index: int, browse: bool = False) -> str:
    index = bounded(index, SIZE, browse)
    if index < len(LOW_CHARACTERS):
        return LOW_CHARACTERS[index]
    code = index - len(LOW_CHARACTERS) + 0x100
    return chr(code + 0x800 if code >= 0xD800 else code)


LETTERS = ascii_lowercase + ascii_uppercase
LOW_CHARACTERS = LETTERS + "".join(
    chr(i) for i in range(0x20, 0x100) if not 0x7F <= i < 0xA0 and chr(i) not in LETTERS
)
SIZE = 0x110000 - 0x800 - 0x41
CHARACTER_GROUPS = [
    (len(LETTERS) * (2 ** (w - 1) - 1), min(SIZE, len(LETTERS) * (2**w - 1)))
    for w in range(1, (1 + (SIZE - 1) // len(LETTERS)).bit_length() + 1)
]
