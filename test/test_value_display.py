import json

import pytest

from nmr.nmr import Nmr
from nmr.web import bridge


def full_index(kind: str, value: str) -> str:
    engine = Nmr()
    result = engine.encode(value, kind, scope="")
    return str(engine.truename_index(result.truename))


def displayed(kind: str, value: str) -> dict:
    return json.loads(bridge.count(json.dumps({"value": full_index(kind, value)})))


def changed(kind: str, value: str, **action: object) -> dict:
    result = json.loads(
        bridge.count_action(json.dumps({"value": full_index(kind, value), **action}))
    )
    count = json.loads(bridge.count(json.dumps({"value": result["index"]})))
    assert result["index"] == full_index(kind, count["browsed"]["value"])
    return count


def test_chess_display_uses_legal_moves_and_move_actions_change_the_full_count() -> (
    None
):
    data = displayed("chess", "")["display"]
    assert len(data["board"]) == 64
    assert len(data["moves"]) == 20
    assert "e2e4" in data["moves"]
    assert data["board"][12] == "P"
    assert not data["undo"]
    moved = changed("chess", "", action="move", move="e2e4")
    assert moved["browsed"]["value"] == "e2e4"
    assert moved["display"]["board"][12] == ""
    assert moved["display"]["board"][28] == "P"
    assert moved["display"]["turn"] == "Black"
    assert changed("chess", "e2e4", action="undo")["browsed"]["value"] == ""
    with pytest.raises(ValueError):
        changed("chess", "", action="move", move="e2e5")


def test_chess_display_preserves_all_four_promotions_and_terminal_games() -> None:
    game = "a2a4 h7h5 a4a5 h5h4 a5a6 h4h3 a6b7 h3g2"
    data = displayed("chess", game)["display"]
    assert {i for i in data["moves"] if i.startswith("b7a8")} == {
        "b7a8b",
        "b7a8n",
        "b7a8q",
        "b7a8r",
    }
    promoted = changed("chess", game, action="move", move="b7a8n")
    assert promoted["display"]["board"][56] == "N"
    terminal = displayed("chess", "f2f3 e7e5 g2g4 d8h4")["display"]
    assert terminal["terminal"]
    assert terminal["moves"] == []


def test_go_display_uses_captures_and_superko_and_undo_preserves_board_size() -> None:
    game = "9x9:C4 C3 E4 E3 D5 D2 A9 D4 D3"
    data = displayed("go", game)["display"]
    assert data["size"] == 9
    assert data["board"][3 * 9 + 3] == 0  # D4 was captured.
    assert "D4" not in data["moves"]  # Immediate ko recapture is illegal.
    terminal = displayed("go", "9x9:pass pass")["display"]
    assert terminal["terminal"]
    assert terminal["moves"] == []
    undone = changed("go", "9x9:pass pass", action="undo")
    assert undone["browsed"]["value"] == "9x9:pass"
    assert "pass" in undone["display"]["moves"]
    moved = changed("go", "9x9:", action="move", move="D4")
    assert moved["browsed"]["value"] == "9x9:D4"
    with pytest.raises(ValueError):
        changed("go", game, action="move", move="D4")


def test_deck_display_and_swaps_follow_original_card_destination_cycles() -> None:
    ordered = displayed("cards", "()")["display"]["cards"]
    assert ordered == list(range(52))
    assert displayed("cards", "(1 2 3)")["display"]["cards"][:3] == [2, 0, 1]
    swapped = changed("cards", "(1 2 3)", action="swap", first=0, second=1)
    assert swapped["browsed"]["value"] == "(2 3)"
    assert swapped["display"]["cards"][:3] == [0, 2, 1]
    with pytest.raises(ValueError):
        changed("cards", "()", action="swap", first=52, second=0)


def test_coordinates_and_other_types_get_their_own_display_data() -> None:
    assert displayed("latlong", "90,0")["display"] == {
        "kind": "latlong",
        "latitude": 90,
        "longitude": 0,
    }
    assert displayed("string", "")["display"] == {
        "kind": "text",
        "type": "string",
        "value": "",
    }
    assert displayed("int", "42")["display"] == {
        "kind": "text",
        "type": "int",
        "value": "42",
    }


@pytest.mark.parametrize(
    "kind,value,action",
    [
        ("int", "0", "move"),
        ("cards", "()", "undo"),
        ("chess", "", "undo"),
        ("go", "9x9:", "undo"),
    ],
)
def test_inapplicable_actions_are_rejected(kind: str, value: str, action: str) -> None:
    with pytest.raises(ValueError):
        changed(kind, value, action=action, move="A1")
