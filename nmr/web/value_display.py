"""Interactive Count displays, derived from the authoritative game codecs."""

from typing import Literal

import chess
from pydantic import BaseModel, Field

from ..types.cards import Cards, rank_permutation, unrank_permutation
from ..types.go import GoBoard


class ValueAction(BaseModel, frozen=True):
    action: Literal["move", "undo", "swap"]
    move: str = ""
    first: int = Field(default=0, ge=0, lt=52)
    second: int = Field(default=0, ge=0, lt=52)


def display_value(kind: str, value: str) -> dict[str, object]:
    if kind == "chess":
        board = chess.Board()
        for token in value.split():
            board.push_uci(token)
        terminal = board.is_game_over(claim_draw=False)
        return {
            "kind": kind,
            "board": [
                i.symbol() if (i := board.piece_at(j)) else "" for j in range(64)
            ],
            "moves": [] if terminal else sorted(i.uci() for i in board.legal_moves),
            "turn": "White" if board.turn else "Black",
            "undo": bool(value),
            "terminal": terminal,
        }
    if kind == "go":
        header, _, moves = value.partition(":")
        board = GoBoard(int(header.split("x")[0]))
        for token in moves.split():
            move = board.parse_move(token)
            board.play(move, board.legal_moves()[move])
        return {
            "kind": kind,
            "size": board.size,
            "board": list(board.stones),
            "moves": [board.format_move(i) for i in board.legal_moves()],
            "turn": "Black" if board.turn == 1 else "White",
            "undo": bool(moves),
            "terminal": board.passes == 2,
        }
    if kind == "cards":
        permutation = unrank_permutation(Cards.str_to_index(value), 52)
        deck = [0] * 52
        for card, destination in enumerate(permutation):
            deck[destination] = card
        return {"kind": kind, "cards": deck}
    if kind == "latlong":
        latitude, longitude = (float(i) for i in value.split(","))
        return {"kind": kind, "latitude": latitude, "longitude": longitude}
    return {"kind": "text", "type": kind, "value": value}


def change_value(kind: str, value: str, request: ValueAction) -> str:
    if request.action == "swap" and kind == "cards":
        permutation = unrank_permutation(Cards.str_to_index(value), 52)
        # The codec maps each original card to its destination position.
        a, b = permutation.index(request.first), permutation.index(request.second)
        permutation[a], permutation[b] = permutation[b], permutation[a]
        return Cards.index_to_str(rank_permutation(permutation))
    if kind not in {"chess", "go"} or request.action == "swap":
        raise ValueError("This action does not apply to this value")
    if request.action == "move":
        if len(request.move.split()) != 1:
            raise ValueError("Choose one move")
        return value + " " + request.move
    prefix = ""
    if kind == "go":
        prefix, _, value = value.partition(":")
        prefix += ":"
    tokens = value.split()
    if not tokens:
        raise ValueError("There is no move to undo")
    return prefix + " ".join(tokens[:-1])
