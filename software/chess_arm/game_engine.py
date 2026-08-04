"""Chess rules and move selection, built on top of python-chess.

If a Stockfish binary is available on PATH (or an explicit path is given),
it's used for the arm's own moves. Otherwise this falls back to picking a
random legal move so the whole pipeline still runs end-to-end without any
extra binaries installed -- handy for demos and for the test suite.
"""

from __future__ import annotations

import logging
import random
import shutil

import chess
import chess.engine

from chess_arm.board_state import BoardDiff

logger = logging.getLogger(__name__)


class GameEngine:
    def __init__(self, stockfish_path: str | None = None):
        self.board = chess.Board()
        self._engine: chess.engine.SimpleEngine | None = None

        path = stockfish_path or shutil.which("stockfish")
        if path:
            self._engine = chess.engine.SimpleEngine.popen_uci(path)
            logger.info("Using Stockfish at %s", path)
        else:
            logger.warning("Stockfish not found; falling back to random legal moves")

    def close(self) -> None:
        if self._engine is not None:
            self._engine.quit()

    def __enter__(self) -> "GameEngine":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def infer_move_from_diff(self, diff: BoardDiff) -> chess.Move | None:
        """Matches a reed-switch diff to a legal move.

        Only the vacated "from" square and occupied "to" square need to
        appear in the diff, so this also matches castling/en passant, which
        touch additional squares (rook, captured pawn) that we simply
        ignore here.
        """
        vacated = set(diff.newly_vacated)
        occupied = set(diff.newly_occupied)

        for move in self.board.legal_moves:
            frm = chess.square_name(move.from_square)
            to = chess.square_name(move.to_square)
            if frm in vacated and to in occupied:
                return move
        return None

    def compute_next_move(self, think_time: float = 1.0) -> chess.Move:
        if self._engine is not None:
            result = self._engine.play(self.board, chess.engine.Limit(time=think_time))
            if result.move is None:
                raise RuntimeError("engine returned no move")
            return result.move
        return random.choice(list(self.board.legal_moves))

    def push(self, move: chess.Move) -> None:
        self.board.push(move)

    @property
    def is_game_over(self) -> bool:
        return self.board.is_game_over()

    @property
    def turn_is_white(self) -> bool:
        return self.board.turn == chess.WHITE
