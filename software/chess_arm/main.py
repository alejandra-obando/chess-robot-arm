"""Entry point: ties the serial link, board sensing, chess engine and move
planner together into a playable game against the arm.

Flow: the human moves a physical piece -> reed switches report the change
-> we match it to a legal move and push it. Then, if it's the arm's turn,
we compute a move, plan its waypoints and stream them to the ESP32.
"""

from __future__ import annotations

import argparse
import logging
import sys

import chess

from chess_arm.board_state import BoardState
from chess_arm.calibration import Calibration
from chess_arm.game_engine import GameEngine
from chess_arm.move_planner import MovePlanner
from chess_arm.serial_link import SerialLink, SerialLinkConfig

logger = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True, help="Serial port, e.g. /dev/ttyUSB0 or COM3")
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument(
        "--calibration",
        default="software/config/calibration.json",
        help="Path to the calibration file produced by scripts/calibrate.py",
    )
    parser.add_argument("--stockfish", default=None, help="Path to a Stockfish binary")
    parser.add_argument(
        "--human-color",
        choices=["white", "black"],
        default="white",
        help="Which side the human plays; the arm plays the other side",
    )
    parser.add_argument("--think-time", type=float, default=1.0, help="Engine think time in seconds")
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> None:
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    calibration = Calibration.load(args.calibration)
    board_state = BoardState()
    planner = MovePlanner(calibration)
    human_is_white = args.human_color == "white"

    link = SerialLink(SerialLinkConfig(port=args.port, baudrate=args.baudrate))
    with link, GameEngine(stockfish_path=args.stockfish) as engine:
        ready = link.wait_for_event("ready", timeout=10.0)
        if ready is None:
            logger.error("Timed out waiting for the ESP32's 'ready' event")
            sys.exit(1)
        logger.info("ESP32 ready: %s", ready)

        logger.info("Game start. Human plays %s.", args.human_color)

        while not engine.is_game_over:
            human_turn = engine.turn_is_white == human_is_white

            if human_turn:
                move = _wait_for_human_move(link, board_state, engine)
                logger.info("Human played %s", move.uci())
                engine.push(move)
            else:
                move = engine.compute_next_move(think_time=args.think_time)
                logger.info("Arm plays %s", move.uci())
                _execute_arm_move(link, planner, move, engine.board)
                engine.push(move)
                board_state.sync_from_board(engine.board)

        logger.info("Game over: %s", engine.board.result())


def _wait_for_human_move(link: SerialLink, board_state: BoardState, engine: GameEngine) -> chess.Move:
    while True:
        event = link.get_event(timeout=None)
        if event is None or event.get("event") != "board":
            continue
        diff = board_state.update(event["state"])
        if diff.is_empty:
            continue
        move = engine.infer_move_from_diff(diff)
        if move is not None:
            return move
        logger.warning(
            "Board change (vacated=%s, occupied=%s) didn't match any legal move; "
            "waiting for the position to settle",
            diff.newly_vacated,
            diff.newly_occupied,
        )


def _execute_arm_move(link: SerialLink, planner: MovePlanner, move: chess.Move, board: chess.Board) -> None:
    for step in planner.plan(move, board):
        link.send_command(step.to_command())
        ack = link.wait_for_event("ack", timeout=5.0)
        if ack is None:
            raise RuntimeError("ESP32 did not ack a move command in time")


def main(argv: list[str] | None = None) -> None:
    run(parse_args(argv))


if __name__ == "__main__":
    main()
