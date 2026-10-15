"""Domain and exact decimal helpers shared by finite codecs."""

from decimal import Decimal, InvalidOperation


def bounded(index: int, size: int, browse: bool) -> int:
    if index < 0:
        raise ValueError("Expected a nonnegative index")
    if browse:
        return index % size
    if index >= size:
        raise ValueError("Index outside the canonical domain; use browse explicitly")
    return index


def scaled_integer(value: str, scale: int) -> int:
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise ValueError("Expected a finite decimal number") from error
    if not number.is_finite():
        raise ValueError("Expected a finite decimal number")
    numerator, denominator = number.as_integer_ratio()
    result, remainder = divmod(numerator * scale, denominator)
    if remainder:
        raise ValueError(f"Value has more precision than 1/{scale}")
    return result


def scaled_string(value: int, scale: int) -> str:
    whole, part = divmod(abs(value), scale)
    digits = len(str(scale)) - 1
    fraction = f"{part:0{digits}d}".rstrip("0")
    return (
        ("-" if value < 0 else "")
        + format(Decimal(whole), "f")
        + ("." + fraction if fraction else "")
    )
