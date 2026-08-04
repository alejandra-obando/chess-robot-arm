import chess

from chess_arm.calibration import Calibration, SquarePose
from chess_arm.move_planner import MovePlanner

STEPS_PER_PICK_AND_PLACE = 8


def make_calibration(squares: list[str], graveyard_slots: int = 1) -> Calibration:
    cal = Calibration(home=[90, 90, 90, 90], gripper_open=40, gripper_closed=120)
    for i, sq in enumerate(squares):
        base = float(i * 10)
        cal.squares[sq] = SquarePose(hover=[base, 60, 90, 90], down=[base, 40, 70, 90])
    for i in range(graveyard_slots):
        cal.graveyard.append(SquarePose(hover=[5.0 + i, 90, 90, 90], down=[5.0 + i, 70, 70, 90]))
    return cal


def test_plan_simple_move_has_one_pick_and_place_plus_return_home():
    board = chess.Board()
    move = chess.Move.from_uci("e2e4")
    cal = make_calibration(["e2", "e4"])
    planner = MovePlanner(cal)

    steps = planner.plan(move, board)

    assert len(steps) == STEPS_PER_PICK_AND_PLACE + 1  # + return-to-home step
    assert steps[-1].angles[:4] == cal.home
    assert steps[-1].angles[4] == cal.gripper_open
    # First waypoint hovers over the source square with the gripper open.
    assert steps[0].angles[:4] == cal.squares["e2"].hover
    assert steps[0].angles[4] == cal.gripper_open


def test_plan_capture_moves_captured_piece_to_graveyard_first():
    # White knight on e5 can capture a black pawn on d7... use a simpler
    # custom position: white pawn e4 captures a black pawn on d5.
    board = chess.Board("8/8/8/3p4/4P3/8/8/8 w - - 0 1")
    move = chess.Move.from_uci("e4d5")
    assert board.is_capture(move)

    cal = make_calibration(["e4", "d5"], graveyard_slots=1)
    planner = MovePlanner(cal)

    steps = planner.plan(move, board)

    # capture pick-and-place (graveyard) + move pick-and-place + home.
    assert len(steps) == 2 * STEPS_PER_PICK_AND_PLACE + 1
    # The very first waypoint hovers over the captured piece's square (d5),
    # not the moving piece's source square (e4).
    assert steps[0].angles[:4] == cal.squares["d5"].hover


def test_plan_en_passant_removes_pawn_from_its_own_square():
    board = chess.Board()
    for san in ["e4", "a6", "e5", "d5"]:
        board.push_san(san)
    move = chess.Move.from_uci("e5d6")
    assert board.is_en_passant(move)

    cal = make_calibration(["e5", "d6", "d5"], graveyard_slots=1)
    planner = MovePlanner(cal)

    steps = planner.plan(move, board)

    assert len(steps) == 2 * STEPS_PER_PICK_AND_PLACE + 1
    # Captured pawn actually sits on d5, one rank behind the destination d6.
    assert steps[0].angles[:4] == cal.squares["d5"].hover


def test_plan_castling_also_moves_the_rook():
    board = chess.Board("4k3/8/8/8/8/8/8/4K2R w K - 0 1")
    move = chess.Move.from_uci("e1g1")
    assert board.is_castling(move)

    cal = make_calibration(["e1", "g1", "h1", "f1"])
    planner = MovePlanner(cal)

    steps = planner.plan(move, board)

    # king pick-and-place + rook pick-and-place + home.
    assert len(steps) == 2 * STEPS_PER_PICK_AND_PLACE + 1
    king_steps = steps[:STEPS_PER_PICK_AND_PLACE]
    rook_steps = steps[STEPS_PER_PICK_AND_PLACE : 2 * STEPS_PER_PICK_AND_PLACE]
    assert king_steps[0].angles[:4] == cal.squares["e1"].hover
    assert rook_steps[0].angles[:4] == cal.squares["h1"].hover


def test_graveyard_slots_are_consumed_in_order_and_raise_when_exhausted():
    board = chess.Board("8/8/8/3p4/4P3/8/8/8 w - - 0 1")
    move = chess.Move.from_uci("e4d5")
    cal = make_calibration(["e4", "d5"], graveyard_slots=0)
    planner = MovePlanner(cal)

    try:
        planner.plan(move, board)
    except RuntimeError:
        pass
    else:
        raise AssertionError("expected RuntimeError when out of graveyard slots")
