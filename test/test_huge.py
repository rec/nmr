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
