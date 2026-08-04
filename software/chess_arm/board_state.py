"""Tracks which squares are physically occupied, from the ESP32's reed
switch matrix, and turns raw matrix diffs into algebraic square names.

The firmware reports a 64-character string of '0'/'1' indexed as
`row * 8 + col` (see docs/protocol.md). Which physical (row, col) is which
chess square depends on how the board was wired and mounted, so that
mapping is configurable here rather than hard-coded in firmware.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import chess

BOARD_SIZE = 8


def default_square_order() -> list[str]:
    """row 0 = rank 8, col 0 = file a -- i.e. looking at the board from
    White's side with the ESP32's row 0 wired to the far (black) side.
    Override this if your matrix is wired differently.
    """
    order = []
    for row in range(BOARD_SIZE):
        rank = BOARD_SIZE - row  # 8, 7, ..., 1
        for col in range(BOARD_SIZE):
            file_index = col  # 0=a .. 7=h
            order.append(chess.square_name(chess.square(file_index, rank - 1)))
    return order


@dataclass
class BoardDiff:
    newly_occupied: list[str] = field(default_factory=list)
    newly_vacated: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.newly_occupied and not self.newly_vacated


class BoardState:
    def __init__(self, square_order: list[str] | None = None):
        self.square_order = square_order or default_square_order()
        if len(self.square_order) != BOARD_SIZE * BOARD_SIZE:
            raise ValueError("square_order must have exactly 64 entries")
        self.occupied: dict[str, bool] = dict.fromkeys(self.square_order, False)

    def update(self, raw_state: str) -> BoardDiff:
        if len(raw_state) != len(self.square_order):
            raise ValueError(
                f"expected a {len(self.square_order)}-char state string, got {len(raw_state)}"
            )

        diff = BoardDiff()
        for square, char in zip(self.square_order, raw_state):
            occupied = char == "1"
            if occupied == self.occupied[square]:
                continue
            self.occupied[square] = occupied
            if occupied:
                diff.newly_occupied.append(square)
            else:
                diff.newly_vacated.append(square)
        return diff

    def sync_from_board(self, board: chess.Board) -> None:
        """Forces the tracked occupancy to match a python-chess Board,
        e.g. right after a move is confirmed to reset drift."""
        for square in self.square_order:
            sq_index = chess.parse_square(square)
            self.occupied[square] = board.piece_at(sq_index) is not None
