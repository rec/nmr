import re

from phonenumbers import phonenumberutil

from ..pack_numbers import rank_digits, unrank_digits
from ..type_truenamer import TypeTruenamer


class Phone(TypeTruenamer):
    label = "phone"
    description = (
        "International phone (+country code, up to 15 digits), optional ;ext=digits"
    )

    @staticmethod
    def str_to_index(value: str) -> int:
        value = value.strip()
        number, separator, extension = value.partition(";ext=")
        if separator and not re.fullmatch(r"[0-9]+", extension):
            raise ValueError("Phone extension must contain digits")
        if not value.startswith("+"):
            raise ValueError("Use an international phone number starting with +")
        # Canonical digits are literal identity, independent of numbering metadata.
        if not re.fullmatch(r"\+[1-9][0-9]{0,14}", number):
            try:
                parsed = phonenumberutil.parse(value, None)
            except phonenumberutil.NumberParseException as error:
                raise ValueError(f"Cannot normalize phone number: {error}") from error
            number = phonenumberutil.format_number(
                parsed, phonenumberutil.PhoneNumberFormat.E164
            )
            extension = parsed.extension or ""
            if not re.fullmatch(r"\+[1-9][0-9]{0,14}", number):
                raise ValueError("International phone numbers allow 1 to 15 digits")
        extra = rank_digits([int(i) for i in extension], 10)
        return int(number[1:]) - 1 + LIMIT * extra

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        extension, number = divmod(index, LIMIT)
        digits = "".join(str(i) for i in unrank_digits(extension, 10))
        return f"+{number + 1}" + (";ext=" + digits if digits else "")


LIMIT = 10**15 - 1
