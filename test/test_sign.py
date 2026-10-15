import pytest

from nmr.words import Words


@pytest.mark.parametrize("n", range(1, 7))
def test_all_unsigned(n: int) -> None:
    engine = Words(count=n)
    for i in range(engine.count_words()):
        assert engine.decode_from_name(engine.encode_to_name(i)) == i
    with pytest.raises(ValueError):
        engine.encode_to_name(-1)
    with pytest.raises(ValueError):
        engine.encode_to_name(engine.count_words())
