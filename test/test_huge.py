import pytest

from nmr.words import Words


def test_vocabulary_capacity_boundary() -> None:
    engine = Words()
    maximum = engine.count_words() - 1
    truename = engine.to_truename(maximum)
    assert len(truename) == engine.count
    assert engine.from_truename(truename) == maximum
    with pytest.raises(ValueError, match="capacity"):
        engine.to_truename(maximum + 1)


@pytest.mark.parametrize(
    "kind,value",
    [("int", "1" + "0" * 4400), ("duration", "1" + "0" * 4400 + "s")],
    ids=["integer", "duration"],
)
def test_numeric_truenames_can_exceed_python_decimal_string_limit(
    kind: str, value: str
) -> None:
    from nmr.nmr import Nmr

    engine = Nmr()
    result = engine.encode(value, kind)
    assert engine.decode(result.truename).value == value
