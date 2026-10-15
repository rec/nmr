import pytest

from nmr.words import Words


def test_vocabulary_capacity_boundary() -> None:
    engine = Words()
    maximum = engine.count_words() - 1
    name = engine.encode_to_name(maximum)
    assert len(name) == engine.count
    assert engine.decode_from_name(name) == maximum
    with pytest.raises(ValueError, match="capacity"):
        engine.encode_to_name(maximum + 1)


@pytest.mark.parametrize(
    "kind,value",
    [("int", "1" + "0" * 4400), ("duration", "1" + "0" * 4400 + "s")],
    ids=["integer", "duration"],
)
def test_numeric_names_can_exceed_python_decimal_string_limit(
    kind: str, value: str
) -> None:
    from nmr.nmr import Nmr

    engine = Nmr()
    result = engine.encode(value, kind)
    assert engine.decode(result.name).value == value
