"""Dense enumeration of Unicode scalar strings; spelling is the value."""

from ..type_namer import TypeNamer


class Text(TypeNamer):
    label = "text"
    description = "Exact text: names, addresses, email, URLs, identifiers, notes"

    @staticmethod
    def str_to_index(value: str) -> int:
        digits = []
        for character in value:
            number = ord(character)
            if 0xD800 <= number < 0xE000:
                raise ValueError("Text cannot contain Unicode surrogate code points")
            digits.append(number if number < 0xD800 else number - 0x800)
        return rank_digits(digits, SCALARS)

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        return "".join(
            chr(i if i < 0xD800 else i + 0x800) for i in unrank_digits(index, SCALARS)
        )


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


SCALARS = 0x110000 - 0x800
