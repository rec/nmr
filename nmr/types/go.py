"""Go play sequences with frozen board sizes, move order, and superko rules."""

import re

from ..type_name import TypeNamer


class Go(TypeNamer):
    label = "go"
    description = "Go moves from an empty board: [19x19:|9x9:|13x13:] D4 Q16 pass"

    @staticmethod
    def str_to_index(value: str) -> int:
        size = 19
        if ":" in value:
            header, value = value.split(":", 1)
            if header.strip() not in [f"{i}x{i}" for i in SIZES]:
                raise ValueError("Go board size must be 19x19, 9x9, or 13x13")
            size = int(header.strip().split("x")[0])
        tokens = value.split()
        if len(tokens) > MAX_PLIES:
            raise ValueError("Go game exceeds the 4096-ply work limit")
        board = GoBoard(size)
        choices = []
        for token in tokens:
            move = board.parse_move(token)
            moves = board.legal_moves()
            if move not in moves:
                raise ValueError(f"Illegal Go move: {token}")
            choices.append((len(moves), list(moves).index(move)))
            board.play(move, moves[move])
        index = 0
        for count, choice in reversed(choices):
            index = 1 + choice + count * index
        return SIZES.index(size) + len(SIZES) * index

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        if index < 0:
            raise ValueError("Go index must be nonnegative")
        index, size_tag = divmod(index, len(SIZES))
        board = GoBoard(SIZES[size_tag])
        tokens = []
        while index:
            if board.passes == 2:
                if browse:
                    break
                raise ValueError("Noncanonical index beyond a terminal Go game")
            if len(tokens) >= MAX_PLIES:
                raise ValueError("Go decode exceeds the 4096-ply work limit")
            moves = board.legal_moves()
            index, choice = divmod(index - 1, len(moves))
            move = list(moves)[choice]
            tokens.append(board.format_move(move))
            board.play(move, moves[move])
        return f"{board.size}x{board.size}:" + " ".join(tokens)


class GoBoard:
    """Alternating play, no suicide, situational superko, two passes end play.

    Legal moves are ordered A1, B1, ..., A2, ... with pass last. Board states
    include the next player for repetition checks. Passing is always legal
    before termination, even when it repeats a state.
    """

    def __init__(self, size: int) -> None:
        self.size = size
        self.stones = bytes(size * size)
        self.turn = 1
        self.passes = 0
        self.history = {(self.stones, self.turn)}
        self.neighbors = []
        for point in range(size * size):
            row, column = divmod(point, size)
            self.neighbors.append(
                [
                    r * size + c
                    for r, c in [
                        (row - 1, column),
                        (row + 1, column),
                        (row, column - 1),
                        (row, column + 1),
                    ]
                    if 0 <= r < size and 0 <= c < size
                ]
            )

    def parse_move(self, token: str) -> int:
        if token.casefold() == "pass":
            return self.size * self.size
        if not re.fullmatch(r"[A-HJ-T][1-9][0-9]?", token.upper()):
            raise ValueError(f"Invalid Go coordinate: {token}")
        column = COLUMNS.index(token[0].upper())
        row = int(token[1:]) - 1
        if column >= self.size or row >= self.size:
            raise ValueError(f"Go coordinate outside the board: {token}")
        return row * self.size + column

    def format_move(self, move: int) -> str:
        if move == self.size * self.size:
            return "pass"
        row, column = divmod(move, self.size)
        return f"{COLUMNS[column]}{row + 1}"

    def legal_moves(self) -> dict[int, bytes]:
        if self.passes == 2:
            return {}
        moves = {}
        for point, stone in enumerate(self.stones):
            if stone:
                continue
            stones = bytearray(self.stones)
            stones[point] = self.turn
            for neighbor in self.neighbors[point]:
                if stones[neighbor] == 3 - self.turn:
                    group, liberties = self._group(stones, neighbor)
                    if not liberties:
                        for captured in group:
                            stones[captured] = 0
            _, liberties = self._group(stones, point)
            state = bytes(stones)
            if liberties and (state, 3 - self.turn) not in self.history:
                moves[point] = state
        moves[self.size * self.size] = self.stones
        return moves

    def play(self, move: int, stones: bytes) -> None:
        """Apply a move and resulting state from legal_moves()."""
        self.passes = self.passes + 1 if move == self.size * self.size else 0
        self.stones = stones
        self.turn = 3 - self.turn
        self.history.add((stones, self.turn))

    def _group(self, stones: bytearray, point: int) -> tuple[set[int], bool]:
        group = {point}
        pending = [point]
        liberties = False
        while pending:
            for neighbor in self.neighbors[pending.pop()]:
                if not stones[neighbor]:
                    liberties = True
                elif stones[neighbor] == stones[point] and neighbor not in group:
                    group.add(neighbor)
                    pending.append(neighbor)
        return group, liberties


# These tags and this ordering are permanent format allocations.
SIZES = (19, 9, 13)
COLUMNS = "ABCDEFGHJKLMNOPQRST"
MAX_PLIES = 4096
