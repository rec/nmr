import pytest

from nmr import nmr, types
from nmr.types import chess

INDICES = 0, 1, 2, 17, 225289, 82394423423, 80983412412323423


@pytest.mark.parametrize("index", INDICES)
def test_rows(index):
    r = chess.index_to_row(index)
    actual = chess.row_to_index(r)
    assert actual == index
