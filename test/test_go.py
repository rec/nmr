import pytest

from nmr.nmr import Nmr
from nmr.types.go import Go, GoBoard


@pytest.mark.parametrize("size", [19, 9, 13])
def test_board_size_and_coordinates_are_preserved(size: int) -> None:
    value = f"{size}x{size}:d4 e4 PASS"
    assert Go.index_to_str(Go.str_to_index(value)) == f"{size}x{size}:D4 E4 pass"
    assert Go.index_to_str(Go.str_to_index(f"{size}x{size}:")) == f"{size}x{size}:"
    assert Go.str_to_index("D4 E4 pass") == Go.str_to_index("19x19:D4 E4 pass")


@pytest.mark.parametrize(
    "value",
    ["8x8:", "9x13:", "I1", "A0", "A01", "A20", "U1", "9x9:K1", "A1 A1"],
)
def test_invalid_moves_are_rejected(value: str) -> None:
    with pytest.raises(ValueError):
        Go.str_to_index(value)


def test_capture_removes_a_connected_group_and_suicide_is_illegal() -> None:
    board = GoBoard(9)
    for token in "B1 A1 C1 A2 B2 pass A3".split():
        move = board.parse_move(token)
        board.play(move, board.legal_moves()[move])
    assert board.stones[board.parse_move("A1")] == 0
    assert board.stones[board.parse_move("A2")] == 0
    with pytest.raises(ValueError, match="Illegal"):
        Go.str_to_index("9x9:B1 A1 A2 A1")


def test_capture_is_allowed_when_it_creates_the_only_liberty() -> None:
    game = "9x9:C4 C3 E4 E3 D5 D2 A9 D4 D3"
    assert Go.index_to_str(Go.str_to_index(game)) == game
    with pytest.raises(ValueError, match="Illegal"):
        Go.str_to_index(game + " D4")
    # A ko threat and response permit recapture with a changed full board.
    continued = game + " A7 A8 D4"
    assert Go.index_to_str(Go.str_to_index(continued)) == continued


def test_passes_end_play_and_terminal_residual_is_browsing_only() -> None:
    canonical = Go.str_to_index("9x9:pass pass")
    # Both positions have 81 empty points and a pass, plus three size tags.
    alias = canonical + 3 * 82**2
    with pytest.raises(ValueError, match="terminal"):
        Go.index_to_str(alias)
    assert Go.index_to_str(alias, browse=True) == "9x9:pass pass"
    with pytest.raises(ValueError, match="Illegal"):
        Go.str_to_index("pass pass A1")
    assert Go.index_to_str(Go.str_to_index("pass A1 pass")) == "19x19:pass A1 pass"


def test_superko_rejects_a_three_ko_cycle() -> None:
    setup = "9x9:B4 B3 D4 D3 C5 C2 F3 F4 H3 H4 G2 G5 G4 C4 B8 B7 D8 D7 C9 C6 J9 C8"
    # Three separated kos allow five captures, but the sixth would repeat
    # the setup position with Black to play, rather than just the last board.
    game = setup + " C3 G3 C7 C4 G4"
    assert Go.index_to_str(Go.str_to_index(game)) == game
    with pytest.raises(ValueError, match="Illegal"):
        Go.str_to_index(game + " C8")


@pytest.mark.parametrize("index", [0, 1, 2, 3, 42, 123456789, 2**256, 2**1000])
def test_browsing_returns_a_canonically_namable_game(index: int) -> None:
    game = Go.index_to_str(index, browse=True)
    assert Go.index_to_str(Go.str_to_index(game)) == game


def test_prefix_scopes_and_custom_words_name_the_same_game() -> None:
    namer = Nmr()
    for scope in [None, "play:game", "play", ""]:
        result = namer.encode("9x9:D4 E4 pass pass", "go", scope)
        assert namer.decode(result.name).value == "9x9:D4 E4 pass pass"
    custom = Nmr(["red", "blue", "green", "gold", "white", "black", "pink"])
    result = custom.encode("A1", "go")
    assert custom.decode(result.name).value == "19x19:A1"


def test_work_limits_and_negative_indices_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="work limit"):
        Go.str_to_index("A1 " * 4097)
    with pytest.raises(ValueError, match="nonnegative"):
        Go.index_to_str(-1)
    monkeypatch.setattr("nmr.types.go.MAX_PLIES", 1)
    with pytest.raises(ValueError, match="work limit"):
        Go.index_to_str(Go.str_to_index("9x9:A1") + 3 * 82)
