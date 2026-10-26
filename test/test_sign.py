import pytest

from nmr.words import Words


@pytest.mark.parametrize("n", range(1, 7))
def test_all_unsigned(n: int) -> None:
    engine = Words(count=n)
    for i in range(engine.count_words()):
        assert engine.from_truename(engine.to_truename(i)) == i
    with pytest.raises(ValueError):
        engine.to_truename(-1)
    with pytest.raises(ValueError):
        engine.to_truename(engine.count_words())
