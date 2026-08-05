import chess

from chess_arm.board_state import BoardState, default_square_order


def _state_with(occupied_squares: set[str]) -> str:
    order = default_square_order()
    return "".join("1" if sq in occupied_squares else "0" for sq in order)


def test_default_square_order_has_64_unique_squares():
    order = default_square_order()
    assert len(order) == 64
    assert len(set(order)) == 64
    assert order[0] == "a8"  # row 0 = rank 8, col 0 = file a
    assert order[-1] == "h1"


def test_update_detects_newly_occupied_and_vacated():
    state = BoardState()
    empty = "0" * 64

    # a8 (index 0) becomes occupied.
    first = "1" + "0" * 63
    diff = state.update(first)
    assert diff.newly_occupied == ["a8"]
    assert diff.newly_vacated == []

    # a8 vacated, h1 (index 63) occupied.
    second = "0" * 63 + "1"
    diff = state.update(second)
    assert diff.newly_vacated == ["a8"]
    assert diff.newly_occupied == ["h1"]

    # No change -> empty diff.
    diff = state.update(second)
    assert diff.is_empty

    diff = state.update(empty)
    assert diff.newly_vacated == ["h1"]


def test_update_rejects_wrong_length():
    state = BoardState()
    try:
        state.update("0" * 10)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for a malformed state string")


def test_sync_from_board_matches_starting_position():
    state = BoardState()
    board = chess.Board()
    state.sync_from_board(board)

    assert state.occupied["e2"] is True  # white pawn
    assert state.occupied["e4"] is False  # empty in the starting position
    assert sum(state.occupied.values()) == 32


def test_isolated_toggle_is_never_suppressed():
    # A real move is always a lone square changing in a given scan -- lateral
    # inhibition must never hold this back, no matter how strong the weight.
    state = BoardState(inhibition_weight=1.0, fire_threshold=0.9)
    diff = state.update(_state_with({"e4"}))
    assert diff.newly_occupied == ["e4"]


def test_simultaneous_adjacent_toggle_is_suppressed_as_crosstalk():
    # e4 and e5 are king-adjacent -- simulates a piece's magnet weakly
    # closing the neighboring square's reed switch in the same scan.
    state = BoardState()
    diff = state.update(_state_with({"e4", "e5"}))
    assert diff.newly_occupied == []
    # Suppressed squares aren't committed, so a later isolated reading
    # for the same square still gets through normally.
    diff = state.update(_state_with({"e4"}))
    assert diff.newly_occupied == ["e4"]


def test_simultaneous_nonadjacent_toggle_is_not_suppressed():
    # a1 and h8 don't compete for the same receptive field, so both fire.
    state = BoardState()
    diff = state.update(_state_with({"a1", "h8"}))
    assert sorted(diff.newly_occupied) == ["a1", "h8"]
