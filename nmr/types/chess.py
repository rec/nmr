"""Legal main-line games, ranked in frozen UCI lexical move order."""

import io
import re

import chess
import chess.pgn

from ..type_name import TypeNamer


class Chess(TypeNamer):
    label = "chess"
    description = "Legal standard-chess move sequence: SAN, UCI, or PGN main line"

    @staticmethod
    def str_to_index(value: str) -> int:
        board = chess.Board()
        choices: list[tuple[int, int]] = []
        tokens: list[str]
        if value.lstrip().startswith("[") or re.search(r"[0-9]+\.", value):
            source = io.StringIO(value)
            game = chess.pgn.read_game(source, Visitor=StrictBuilder)
            if game is None:
                raise ValueError("No PGN game found")
            if game.board().fen() != board.fen():
                raise ValueError(
                    "Chess games must start from the standard initial position"
                )
            if source.read().strip():
                raise ValueError("Provide only one PGN game")
            tokens = [i.uci() for i in game.mainline_moves()]
        else:
            tokens = value.split()
        if len(tokens) > MAX_PLIES:
            raise ValueError("Chess game exceeds the 4096-ply work limit")
        for token in tokens:
            if board.is_game_over(claim_draw=False):
                raise ValueError("Moves cannot follow an automatic game ending")
            moves = sorted(board.legal_moves, key=chess.Move.uci)
            move = board.parse_san(token)
            choices.append((len(moves), moves.index(move)))
            board.push(move)
        index = 0
        for count, choice in reversed(choices):
            index = 1 + choice + count * index
        return index

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        board = chess.Board()
        tokens = []
        while index:
            if board.is_game_over(claim_draw=False):
                if browse:
                    break
                raise ValueError("Noncanonical index beyond a terminal chess game")
            if len(tokens) >= MAX_PLIES:
                raise ValueError("Chess decode exceeds the 4096-ply work limit")
            moves = sorted(board.legal_moves, key=chess.Move.uci)
            index, choice = divmod(index - 1, len(moves))
            move = moves[choice]
            tokens.append(move.uci())
            board.push(move)
        return " ".join(tokens)


class StrictBuilder(chess.pgn.GameBuilder):
    def handle_error(self, error: Exception) -> None:
        raise ValueError(f"Invalid PGN: {error}") from error


MAX_PLIES = 4096
