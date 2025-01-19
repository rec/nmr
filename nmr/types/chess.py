import chess

from ..categories import Game
from ..nameable_type import NameableType


class Chess(NameableType[chess.Board]):
    category = Game.CHESS

    @staticmethod
    def index_to_type(i: int) -> chess.Board:
        return chess.Board()

    @staticmethod
    def type_to_str(board: chess.Board) -> str:
        return board.fen()

    @staticmethod
    def type_to_index(n: chess.Board) -> int:
        board, move, castle, en_passant, half_move, move = b.fen().split()


ALPHABET = "12345678BKNPQRbknpqr"
RADIX = len(ALPHABET) ** 8


def row_to_index(row: str) -> int:
    total = 0
    for c in row:
        total = total * len(ALPHABET) + ALPHABET.index(c)
    return total


def index_to_row(i: int) -> str:
    row: list[str] = []
    while i:
        i, r = divmod(i, len(ALPHABET))
        row.append(ALPHABET[r])
    return "".join(reversed(row))
