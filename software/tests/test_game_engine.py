import chess

from chess_arm.board_state import BoardDiff
from chess_arm.game_engine import GameEngine


def test_infer_move_from_diff_matches_legal_move():
    with GameEngine() as engine:  # no stockfish -> falls back to random moves
        diff = BoardDiff(newly_vacated=["e2"], newly_occupied=["e4"])
        move = engine.infer_move_from_diff(diff)
        assert move == chess.Move.from_uci("e2e4")


def test_infer_move_from_diff_returns_none_for_illegal_change():
    with GameEngine() as engine:
        diff = BoardDiff(newly_vacated=["e2"], newly_occupied=["e5"])
        assert engine.infer_move_from_diff(diff) is None


def test_compute_next_move_returns_a_legal_move_without_stockfish():
    with GameEngine() as engine:
        move = engine.compute_next_move(think_time=0.01)
        assert move in engine.board.legal_moves


def test_turn_is_white_toggles_after_push():
    with GameEngine() as engine:
        assert engine.turn_is_white is True
        engine.push(chess.Move.from_uci("e2e4"))
        assert engine.turn_is_white is False
