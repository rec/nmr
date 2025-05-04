import pytest

from nmr.types.time import formats

ROUND_TRIPS = ()


@pytest.mark.parametrize("s", ROUND_TRIPS)
def test_index_roundtrips(s):
    i = types.str_to_index(s)
    assert s == types.index_to_str(i)
