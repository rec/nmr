import pytest
from chess import Board

from nmr import nmr
from nmr.types import chess

INDICES = 0, 1, 2, 17, 225289, 82394423423
COUNT = 10


def _begin(a):
    return a[0]


def _middle(a):
    return a[int(len(a) / 2)]


def _end(a):
    return a[-1]


@pytest.mark.parametrize("index", INDICES)
def test_rows(index):
    r = chess.index_to_row(index)
    actual = chess.row_to_index(r)
    assert actual == index, r


def test_basic():
    b = Board()
    name = nmr.str_to_name(b.fen())
    b2 = nmr.name_to_str(name)
    assert b2 == b.fen()


@pytest.mark.parametrize("strategy", (_begin, _middle, _end))
def test_full_roundtrip(strategy):
    b = Board()

    while not b.can_claim_draw() and (moves := list(b.legal_moves)):
        b.push(strategy(moves))
        name = nmr.str_to_name(b.fen())
        b2 = nmr.name_to_str(name)
        assert b2 == b.fen()


def test_enpassant():
    b = Board()
    fens = []

    for m in "e4 a5 f4 a4 b4 axb3".split():
        fens.append(b.fen())
        b.push_san(m)
        name = nmr.str_to_name(b.fen())
        b2 = nmr.name_to_str(name)
        assert b2 == b.fen()
