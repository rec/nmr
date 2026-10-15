import re

from ..type_namer import TypeNamer
from .text import rank_digits, unrank_digits


class Phone(TypeNamer):
    label = "phone"
    description = (
        "International phone (+country code, up to 15 digits), optional ;ext=digits"
    )

    @staticmethod
    def str_to_index(value: str) -> int:
        number, separator, extension = value.partition(";ext=")
        number = re.sub(r"[ ()-]", "", number)
        if not re.fullmatch(r"\+[1-9][0-9]{0,14}", number):
            raise ValueError(
                "Use + followed by 1 to 15 digits, starting with a nonzero digit"
            )
        if separator and not re.fullmatch(r"[0-9]+", extension):
            raise ValueError("Phone extension must contain digits")
        extra = rank_digits([int(i) for i in extension], 10)
        return int(number[1:]) - 1 + LIMIT * extra

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        extension, number = divmod(index, LIMIT)
        digits = "".join(str(i) for i in unrank_digits(extension, 10))
        return f"+{number + 1}" + (";ext=" + digits if digits else "")


LIMIT = 10**15 - 1
