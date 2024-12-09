import pytest

from nmr import Nmr


@pytest.mark.parametrize("n", range(1, 7))
def test_all_unsigned(n):
    N = Nmr(n)
    m = N.count(n)

    for i in range(m):
        words = N.encode_to_name(i)
        assert len(words) == len(set(words))
        assert N.decode_from_name(words) == i, str(words)

    err = "Only accepts non-negative numbers"
    with pytest.raises(ValueError, match=err):
        N.encode_to_name(-1)

    err = f"Cannot represent {m} in base {n}"
    with pytest.raises(ValueError, match=err):
        N.encode_to_name(m)
