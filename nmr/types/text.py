"""UTF-8 text with sparse canonical indices; spelling is the value."""

from ..type_namer import TypeNamer


class Text(TypeNamer):
    label = "text"
    description = "Exact text: names, addresses, email, URLs, identifiers, notes"

    @staticmethod
    def str_to_index(value: str) -> int:
        return rank_digits(list(value.encode()), 256)

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        data = bytes(unrank_digits(index, 256))
        if not browse:
            return data.decode()
        parts = []
        while data:
            try:
                parts.append(data.decode())
                break
            except UnicodeDecodeError as error:
                parts.extend([data[: error.start].decode(), "?"])
                data = data[error.end :]
        return "".join(parts)


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
