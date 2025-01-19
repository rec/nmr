import chess

from ..categories import Game
from ..nameable_type import NameableType
from ..radixes import Radixes


class Chess(NameableType[chess.Board]):
    category = Game.CHESS

    @staticmethod
    def type_to_str(board: chess.Board) -> str:
        return board.fen()

    @staticmethod
    def type_to_index(b: chess.Board) -> int:
        board, side, castle, ep, half_move, move = b.fen().split()
        parts = (
            int(move),
            int(half_move),
            en_passant_to_index(ep),
            *(c in castle for c in CASTLES),
            SIDES.index(side),
            *(row_to_index(b) for b in board.split("/")),
        )
        ret = RADIXES.encode(*parts)
        return ret

    @staticmethod
    def index_to_type(n: int) -> chess.Board:
        parts = RADIXES.decode(n)
        parts, board = parts[:-8], parts[-8:]
        move, half_move, ep, *castle, side = parts
        assert len(castle) == 4
        fields = (
            "/".join(index_to_row(r) for r in board),
            SIDES[side],
            "".join(c for b, c in zip(castle, CASTLES) if b) or "-",
            index_to_en_passant(ep),
            str(half_move),
            str(move),
        )
        return chess.Board(" ".join(fields))


ALPHABET = "12345678BKNPQRbknpqr"
SIDES = "wb"
CASTLES = "KQkq"
EP_LENGTH = 65
ROW_RADIX = (1 + len(ALPHABET)) ** 8

RADIXES = Radixes(51, EP_LENGTH, *(2 for c in CASTLES), len(SIDES), *(8 * [ROW_RADIX]))


def en_passant_to_index(ep: str) -> int:
    if ep == "-":
        return 0

    assert len(ep) == 2
    col, row = ep[0], ep[1]
    r = int(row) - 1
    c = ord(col) - ord("a")
    return 1 + 8 * r + c  # TODO: or the reverse?


def index_to_en_passant(i: int) -> str:
    if i == 0:
        return "-"
    r, c = divmod(i - 1, 8)
    col = chr(ord("a") + c)
    row = str(r + 1)
    return f"{col}{row}"


def row_to_index(row: str) -> int:
    total = 0
    for c in row:
        total = total * (len(ALPHABET) + 1) + ALPHABET.index(c) + 1
    return total


def index_to_row(i: int) -> str:
    row: list[str] = []
    while i:
        i, r = divmod(i, len(ALPHABET) + 1)
        if not r:
            break
        row.append(ALPHABET[r - 1])
    return "".join(reversed(row))
