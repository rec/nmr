import re

from ..type_truenamer import TypeTruenamer
from .bounded import bounded


class Isbn(TypeTruenamer):
    label = "isbn"
    description = (
        "ISBN-10 or ISBN-13 with a valid check digit (assignment is not checked)"
    )

    @staticmethod
    def str_to_index(value: str) -> int:
        value = value.replace("-", "").replace(" ", "").upper()
        if re.fullmatch(r"[0-9]{9}[0-9X]", value):
            expected = isbn10_check(value[:9])
            if value[-1] != expected:
                raise ValueError("Invalid ISBN-10 check digit")
            return int(value[:9])
        if re.fullmatch(r"97[89][0-9]{10}", value):
            if value[-1] != retail_check(value[:12]):
                raise ValueError("Invalid ISBN-13 check digit")
            return BILLION + (int(value[:3]) - 978) * BILLION + int(value[3:12])
        raise ValueError("Expected ISBN-10 or ISBN-13 beginning 978 or 979")

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        index = bounded(index, 3 * BILLION, browse)
        if index < BILLION:
            body = f"{index:09d}"
            return body + isbn10_check(body)
        group, suffix = divmod(index - BILLION, BILLION)
        body = f"{978 + group}{suffix:09d}"
        return body + retail_check(body)


class Upc(TypeTruenamer):
    label = "upc"
    description = "UPC-A: 12 digits including its check digit"

    @staticmethod
    def str_to_index(value: str) -> int:
        value = value.replace(" ", "").replace("-", "")
        if not re.fullmatch(r"[0-9]{12}", value) or value[-1] != retail_check(
            value[:11]
        ):
            raise ValueError("Expected a valid 12-digit UPC-A")
        return int(value[:11])

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        body = f"{bounded(index, 10**11, browse):011d}"
        return body + retail_check(body)


def retail_check(body: str) -> str:
    return str(
        -sum(int(c) * (3 if i % 2 == 0 else 1) for i, c in enumerate(reversed(body)))
        % 10
    )


def isbn10_check(body: str) -> str:
    digit = -sum(int(c) * (10 - i) for i, c in enumerate(body)) % 11
    return "X" if digit == 10 else str(digit)


BILLION = 10**9
