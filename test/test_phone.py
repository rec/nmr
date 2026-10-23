import pytest
from pytest import MonkeyPatch

from nmr.nmr import Nmr
from nmr.types.phone_number import Phone


@pytest.mark.parametrize(
    "value,canonical",
    [
        ("+44 (0)20 7946 0958", "+442079460958"),
        ("+33 (0)1 42 34 56 78", "+33142345678"),
        ("+39 02 36618 300", "+390236618300"),
        ("+1-800-FLOWERS", "+18003569377"),
        ("+44.20.7946.0958 ext. 004", "+442079460958;ext=004"),
        ("+44 (20) 7946-0958;ext=004", "+442079460958;ext=004"),
        ("+٤٤ ٢٠ ٧٩٤٦ ٠٩٥٨", "+442079460958"),
    ],
)
def test_international_formats_normalize_to_the_same_named_digits(
    value: str, canonical: str
) -> None:
    engine = Nmr()
    result = engine.encode(value, "phone")
    assert result.value == canonical
    assert result.name == engine.encode(canonical, "phone").name
    assert engine.decode(result.name).value == canonical


@pytest.mark.parametrize(
    "value",
    [
        "020 7946 0958",
        "0044 20 7946 0958",
        "+not a number",
        "+44 20 7946 0958;ext=",
        "+442079460958;ext=004;ext=005",
        "+1234567890123456",
    ],
)
def test_invalid_or_ambiguous_phone_input_is_rejected(value: str) -> None:
    with pytest.raises(ValueError):
        Phone.str_to_index(value)


def test_canonical_digits_decode_without_numbering_metadata(
    monkeypatch: MonkeyPatch,
) -> None:
    def unavailable(*args: object, **kwargs: object) -> None:
        raise AssertionError("Canonical identity must not use the library")

    monkeypatch.setattr("nmr.types.phone_number.phonenumberutil.parse", unavailable)
    engine = Nmr()
    for value in ["+1", "+999123456789012", "+442079460958;ext=004"]:
        result = engine.encode(value, "phone")
        assert result.value == value
        assert engine.decode(result.name).value == value
