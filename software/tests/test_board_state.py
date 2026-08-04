import chess

from chess_arm.board_state import BoardState, default_square_order


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
