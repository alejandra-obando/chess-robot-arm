"""Tracks which squares are physically occupied, from the ESP32's reed
switch matrix, and turns raw matrix diffs into algebraic square names.

The firmware reports a 64-character string of '0'/'1' indexed as
`row * 8 + col` (see docs/protocol.md). Which physical (row, col) is which
chess square depends on how the board was wired and mounted, so that
mapping is configurable here rather than hard-coded in firmware.

Before a raw diff is trusted, it goes through a small lateral-inhibition
step (see `_lateral_inhibition`): a piece's magnet sitting near a square's
edge can weakly close a neighboring reed switch too, so two adjacent
squares occasionally toggle in the very same scan. A human can't move two
pieces within one 50 ms scan tick, so a genuine move is always an isolated
toggle; simultaneous same-direction toggles on neighboring squares are
almost always that crosstalk, and get suppressed the same way a
center-surround receptive field suppresses a weak signal next to a
stronger one, rather than by hard-coding a debounce heuristic.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import chess

BOARD_SIZE = 8

# How strongly a simultaneously-toggled neighbor suppresses a square's
# evidence, and how much net activation a square needs to still "fire"
# after that suppression. An isolated toggle (no firing neighbors) always
# has net activation 1.0, so it always passes regardless of these values.
DEFAULT_INHIBITION_WEIGHT = 0.5
DEFAULT_FIRE_THRESHOLD = 0.6


def _king_neighbors(square: str) -> list[str]:
    """The up-to-8 adjacent squares (a king's reachable squares), used as
    the receptive-field surround for lateral inhibition."""
    sq_index = chess.parse_square(square)
    file_index, rank_index = chess.square_file(sq_index), chess.square_rank(sq_index)
    neighbors = []
    for d_file in (-1, 0, 1):
        for d_rank in (-1, 0, 1):
            if d_file == 0 and d_rank == 0:
                continue
            nf, nr = file_index + d_file, rank_index + d_rank
            if 0 <= nf < BOARD_SIZE and 0 <= nr < BOARD_SIZE:
                neighbors.append(chess.square_name(chess.square(nf, nr)))
    return neighbors


def _lateral_inhibition(
    candidates: list[str], weight: float, threshold: float
) -> list[str]:
    """Center-surround competition among squares that toggled in the same
    direction (occupied or vacated) within a single scan. Each candidate
    starts with activation 1.0 and loses `weight` for every candidate
    neighbor also firing this scan; only candidates whose net activation
    stays above `threshold` survive.

    Note: this also suppresses genuinely simultaneous same-direction moves
    on adjacent squares, e.g. castling's f1+g1 (or c1/d1) pair -- accepted
    here since in practice that pair arrives as two separate scans (a
    human can't move both pieces within 50 ms).
    """
    candidate_set = set(candidates)
    survivors = []
    for square in candidates:
        firing_neighbors = sum(1 for n in _king_neighbors(square) if n in candidate_set)
        net_activation = 1.0 - weight * firing_neighbors
        if net_activation > threshold:
            survivors.append(square)
    return survivors


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
    def __init__(
        self,
        square_order: list[str] | None = None,
        inhibition_weight: float = DEFAULT_INHIBITION_WEIGHT,
        fire_threshold: float = DEFAULT_FIRE_THRESHOLD,
    ):
        self.square_order = square_order or default_square_order()
        if len(self.square_order) != BOARD_SIZE * BOARD_SIZE:
            raise ValueError("square_order must have exactly 64 entries")
        self.occupied: dict[str, bool] = dict.fromkeys(self.square_order, False)
        self.inhibition_weight = inhibition_weight
        self.fire_threshold = fire_threshold

    def update(self, raw_state: str) -> BoardDiff:
        if len(raw_state) != len(self.square_order):
            raise ValueError(
                f"expected a {len(self.square_order)}-char state string, got {len(raw_state)}"
            )

        occupied_candidates = []
        vacated_candidates = []
        for square, char in zip(self.square_order, raw_state):
            occupied = char == "1"
            if occupied == self.occupied[square]:
                continue
            (occupied_candidates if occupied else vacated_candidates).append(square)

        diff = BoardDiff()
        for square in _lateral_inhibition(
            occupied_candidates, self.inhibition_weight, self.fire_threshold
        ):
            self.occupied[square] = True
            diff.newly_occupied.append(square)
        for square in _lateral_inhibition(
            vacated_candidates, self.inhibition_weight, self.fire_threshold
        ):
            self.occupied[square] = False
            diff.newly_vacated.append(square)
        return diff

    def sync_from_board(self, board: chess.Board) -> None:
        """Forces the tracked occupancy to match a python-chess Board,
        e.g. right after a move is confirmed to reset drift."""
        for square in self.square_order:
            sq_index = chess.parse_square(square)
            self.occupied[square] = board.piece_at(sq_index) is not None
