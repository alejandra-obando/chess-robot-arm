#!/usr/bin/env python3
"""Interactive tool to build software/config/calibration.json.

Jogs the arm to angles you type in (previewed live over serial) and saves
them as the hover/down pose for a square or a graveyard slot. Re-run it any
time to add more squares to an existing calibration file.

Only talks to the arm ESP32 (firmware/esp32_arm) -- the board ESP32 isn't
involved in calibration.

Usage:
    python scripts/calibrate.py --arm-port /dev/ttyUSB1
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "software"))

from chess_arm.calibration import Calibration, SquarePose  # noqa: E402
from chess_arm.serial_link import SerialLink, SerialLinkConfig  # noqa: E402


def prompt_angles(label: str, current: list[float]) -> list[float]:
    raw = input(f"{label} angles [base,shoulder,elbow,wrist] (blank = keep {current}): ").strip()
    if not raw:
        return current
    return [float(x) for x in raw.split(",")]


def send_preview(link: SerialLink, arm_angles: list[float], gripper_angle: float) -> None:
    link.send_command({"cmd": "move", "angles": [*arm_angles, gripper_angle], "duration_ms": 500})
    link.wait_for_event("ack", timeout=5.0)


def save_square(cal: Calibration, square: str, pose_type: str, angles: list[float]) -> None:
    pose = cal.squares.get(square)
    if pose is None:
        pose = SquarePose(hover=list(angles), down=list(angles))
        cal.squares[square] = pose
    if pose_type == "down":
        pose.down = list(angles)
    else:
        pose.hover = list(angles)


def save_graveyard(cal: Calibration, pose_type: str, angles: list[float]) -> None:
    if not cal.graveyard or input("New slot? [y/N]: ").strip().lower() == "y":
        cal.graveyard.append(SquarePose(hover=list(angles), down=list(angles)))
    pose = cal.graveyard[-1]
    if pose_type == "down":
        pose.down = list(angles)
    else:
        pose.hover = list(angles)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm-port", required=True, help="Arm ESP32 serial port, e.g. /dev/ttyUSB1")
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument("--out", default="software/config/calibration.json")
    args = parser.parse_args()

    out_path = Path(args.out)
    if out_path.exists():
        cal = Calibration.load(out_path)
        print(f"Loaded existing calibration from {out_path}")
    else:
        cal = Calibration(home=[90, 90, 90, 90], gripper_open=40, gripper_closed=120)
        print("Starting a new calibration file.")

    link = SerialLink(SerialLinkConfig(port=args.arm_port, baudrate=args.baudrate))
    with link:
        ready = link.wait_for_event("ready", timeout=10.0)
        if ready is None:
            print("Timed out waiting for the arm ESP32.")
            return
        print("Arm ESP32 ready:", ready)

        current = list(cal.home)
        gripper = cal.gripper_open

        while True:
            print("\nCommands: [g]o to angles, [h]ome, [s]ave current pose, [q]uit")
            cmd = input("> ").strip().lower()

            if cmd == "q":
                break
            elif cmd == "h":
                current = list(cal.home)
                send_preview(link, current, gripper)
            elif cmd == "g":
                current = prompt_angles("Preview", current)
                gripper_raw = input(f"Gripper angle (blank = keep {gripper}): ").strip()
                gripper = float(gripper_raw) if gripper_raw else gripper
                send_preview(link, current, gripper)
            elif cmd == "s":
                target = input("Save as (square like e4, or 'graveyard'): ").strip()
                pose_type = input("Pose type ([hover]/down): ").strip() or "hover"
                if target == "graveyard":
                    save_graveyard(cal, pose_type, current)
                else:
                    save_square(cal, target, pose_type, current)
                cal.save(out_path)
                print(f"Saved. Calibration written to {out_path}")
            else:
                print("Unknown command")

    cal.save(out_path)
    print(f"Done. Final calibration written to {out_path}")


if __name__ == "__main__":
    main()
