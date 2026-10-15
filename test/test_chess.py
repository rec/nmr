import chess
import pytest

from nmr.types.chess import Chess


def test_browsed_games_are_reachable() -> None:
    for index in [0, 1, 20, 21, 123456789, 2**256, 2**1000]:
        board = chess.Board()
        sequence = Chess.index_to_str(index, browse=True)
        for move in sequence.split():
            board.push_uci(move)
            assert board.is_valid()
        canonical = Chess.str_to_index(sequence)
        assert Chess.index_to_str(canonical) == sequence


def test_terminal_overrun_is_browsing_only() -> None:
    game = "f3 e5 g4 Qh4#"
    canonical = Chess.str_to_index(game)
    # A positive residual at the terminal position follows the same moves.
    board = chess.Board()
    weight = 1
    for token in game.split():
        weight *= board.legal_moves.count()
        board.push_san(token)
    with pytest.raises(ValueError, match="terminal"):
        Chess.index_to_str(canonical + weight)
    assert Chess.index_to_str(canonical + weight, browse=True) == Chess.index_to_str(
        canonical
    )


def test_pgn_mainline_and_special_moves() -> None:
    assert Chess.str_to_index("1. e4 e5 2. Nf3 *") == Chess.str_to_index("e4 e5 Nf3")
    sequence = "e4 a5 e5 d5 exd6 cxd6 Nf3 Nf6 Be2 e6 O-O"
    assert Chess.index_to_str(Chess.str_to_index(sequence)).split()[-1] == "e1g1"


def test_promotion_preserves_the_selected_piece() -> None:
    game = "a4 h5 a5 h4 a6 h3 axb7 hxg2 bxa8=Q"
    assert Chess.index_to_str(Chess.str_to_index(game)).split()[-1] == "b7a8q"
