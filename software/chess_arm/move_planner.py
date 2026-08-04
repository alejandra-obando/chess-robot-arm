"""Turns a chess.Move into a sequence of arm waypoints (a "pick and place"),
handling plain moves, captures, en passant and castling.

Promotions are treated as a plain move -- the arm keeps using the pawn's
physical piece, since swapping it for a queen piece mid-game is a manual
step outside this project's scope.
"""

from __future__ import annotations

from dataclasses import dataclass

import chess

from chess_arm.calibration import Calibration, SquarePose

# to_square -> (rook_from, rook_to) for each of the four castling moves.
_CASTLING_ROOK_SQUARES = {
    chess.G1: (chess.H1, chess.F1),
    chess.C1: (chess.A1, chess.D1),
    chess.G8: (chess.H8, chess.F8),
    chess.C8: (chess.A8, chess.D8),
}


@dataclass
class MotionStep:
    angles: list[float]
    duration_ms: int

    def to_command(self) -> dict:
        return {"cmd": "move", "angles": self.angles, "duration_ms": self.duration_ms}


class MovePlanner:
    def __init__(self, calibration: Calibration):
        self.calibration = calibration
        self._next_graveyard_slot = 0

    def reset(self) -> None:
        """Call at the start of a new game to reuse graveyard slots."""
        self._next_graveyard_slot = 0

    def plan(self, move: chess.Move, board: chess.Board) -> list[MotionStep]:
        """`board` must be the position *before* `move` is pushed, so
        is_capture/is_en_passant/is_castling can be evaluated."""
        cal = self.calibration
        steps: list[MotionStep] = []

        if board.is_en_passant(move):
            captured_square = chess.square(
                chess.square_file(move.to_square), chess.square_rank(move.from_square)
            )
            steps += self._pick_and_place(
                cal.pose_for_square(chess.square_name(captured_square)),
                self._take_graveyard_slot(),
            )
        elif board.is_capture(move):
            steps += self._pick_and_place(
                cal.pose_for_square(chess.square_name(move.to_square)),
                self._take_graveyard_slot(),
            )

        steps += self._pick_and_place(
            cal.pose_for_square(chess.square_name(move.from_square)),
            cal.pose_for_square(chess.square_name(move.to_square)),
        )

        if board.is_castling(move):
            rook_from, rook_to = _CASTLING_ROOK_SQUARES[move.to_square]
            steps += self._pick_and_place(
                cal.pose_for_square(chess.square_name(rook_from)),
                cal.pose_for_square(chess.square_name(rook_to)),
            )

        steps.append(MotionStep(self._with_gripper(cal.home, cal.gripper_open), cal.move_duration_ms))
        return steps

    def _take_graveyard_slot(self) -> SquarePose:
        cal = self.calibration
        if self._next_graveyard_slot >= len(cal.graveyard):
            raise RuntimeError("out of graveyard slots for captured pieces")
        slot = cal.graveyard[self._next_graveyard_slot]
        self._next_graveyard_slot += 1
        return slot

    def _pick_and_place(self, source: SquarePose, dest: SquarePose) -> list[MotionStep]:
        cal = self.calibration
        open_, closed = cal.gripper_open, cal.gripper_closed
        return [
            MotionStep(self._with_gripper(source.hover, open_), cal.hover_duration_ms),
            MotionStep(self._with_gripper(source.down, open_), cal.move_duration_ms),
            MotionStep(self._with_gripper(source.down, closed), cal.move_duration_ms),
            MotionStep(self._with_gripper(source.hover, closed), cal.hover_duration_ms),
            MotionStep(self._with_gripper(dest.hover, closed), cal.hover_duration_ms),
            MotionStep(self._with_gripper(dest.down, closed), cal.move_duration_ms),
            MotionStep(self._with_gripper(dest.down, open_), cal.move_duration_ms),
            MotionStep(self._with_gripper(dest.hover, open_), cal.hover_duration_ms),
        ]

    @staticmethod
    def _with_gripper(arm_angles: list[float], gripper_angle: float) -> list[float]:
        return [*arm_angles, gripper_angle]
