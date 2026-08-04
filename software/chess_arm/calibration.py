"""Loads/saves the servo-angle calibration: for each square (and each
"graveyard" slot where captured pieces get parked), the arm's hover angles
(safely above the board) and down angles (low enough to grab/release a
piece).

The gripper isn't part of a square's pose -- it only ever needs an "open"
and a "closed" angle, applied on top of whichever arm pose is active. See
scripts/calibrate.py for the interactive tool that generates this file.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

NUM_ARM_JOINTS = 4  # base, shoulder, elbow, wrist -- gripper is separate


@dataclass
class SquarePose:
    hover: list[float]
    down: list[float]

    def __post_init__(self) -> None:
        for name, angles in (("hover", self.hover), ("down", self.down)):
            if len(angles) != NUM_ARM_JOINTS:
                raise ValueError(f"{name} pose must have {NUM_ARM_JOINTS} angles, got {len(angles)}")


@dataclass
class Calibration:
    home: list[float]
    gripper_open: float
    gripper_closed: float
    squares: dict[str, SquarePose] = field(default_factory=dict)
    graveyard: list[SquarePose] = field(default_factory=list)
    hover_duration_ms: int = 800
    move_duration_ms: int = 600

    def pose_for_square(self, square: str) -> SquarePose:
        try:
            return self.squares[square]
        except KeyError as exc:
            raise KeyError(
                f"no calibration for square '{square}' -- run scripts/calibrate.py"
            ) from exc

    @classmethod
    def load(cls, path: str | Path) -> "Calibration":
        data = json.loads(Path(path).read_text())
        return cls(
            home=data["home"],
            gripper_open=data["gripper_open"],
            gripper_closed=data["gripper_closed"],
            squares={sq: SquarePose(**pose) for sq, pose in data.get("squares", {}).items()},
            graveyard=[SquarePose(**pose) for pose in data.get("graveyard", [])],
            hover_duration_ms=data.get("hover_duration_ms", 800),
            move_duration_ms=data.get("move_duration_ms", 600),
        )

    def save(self, path: str | Path) -> None:
        data = {
            "home": self.home,
            "gripper_open": self.gripper_open,
            "gripper_closed": self.gripper_closed,
            "squares": {sq: asdict(pose) for sq, pose in self.squares.items()},
            "graveyard": [asdict(pose) for pose in self.graveyard],
            "hover_duration_ms": self.hover_duration_ms,
            "move_duration_ms": self.move_duration_ms,
        }
        Path(path).write_text(json.dumps(data, indent=2) + "\n")
