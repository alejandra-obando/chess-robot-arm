# Serial protocol

There are **two independent** newline-delimited JSON links, one per ESP32 --
they are separate USB serial ports and the PC talks to each on its own
`SerialLink` instance (`--board-port` and `--arm-port`, see the root
README). The two ESP32s never talk to each other. Every message, on either
link, is a single JSON object followed by `\n`, at **115200 baud**.

Both boards are intentionally "dumb": the board ESP32 only reports raw
occupancy, and the arm ESP32 only executes joint-angle commands. All chess
rules and motion planning live on the PC (`software/chess_arm/`).

## Board link (`firmware/esp32_board`)

### ESP32 -> PC: `ready`

Sent once at boot, after the reed matrix is initialized.

```json
{"event": "ready", "board_size": 8}
```

### ESP32 -> PC: `board`

Sent whenever the reed-switch matrix scan detects a change. `state` is a
64-character string of `'0'`/`'1'`, indexed `row * board_size + col`
(row-major). Mapping `(row, col)` to algebraic squares (a1, e4, ...) is a
PC-side concern -- see `chess_arm.board_state.default_square_order` -- since
it depends on how the board was physically wired.

```json
{"event": "board", "state": "0000000000000000000000000000000000000000000000000000000000000000"}
```

(real strings are 64 characters; shortened here for readability)

### PC -> ESP32: `ping` / ESP32 -> PC: `pong`

Liveness check, same shape as the arm link below.

### ESP32 -> PC: `error`

Sent when a command couldn't be parsed or was invalid.

## Arm link (`firmware/esp32_arm`)

### PC -> ESP32: `move`

Moves all 5 logical joints to the given angles, interpolating smoothly over
`duration_ms`.

```json
{"cmd": "move", "angles": [90, 45, 120, 90, 40], "duration_ms": 800}
```

- `angles` has exactly `NUM_JOINTS` entries (5: base, shoulder, elbow,
  wrist, gripper -- see `firmware/esp32_arm/src/config.h`), in degrees.
  The shoulder angle is internally mirrored to its two PCA9685 channels;
  the PC never needs to know the shoulder has two physical servos.
- `duration_ms` is optional, default `800`.

### PC -> ESP32: `ping`

```json
{"cmd": "ping"}
```

Used as a liveness check; the ESP32 replies with a `pong` event.

### ESP32 -> PC: `ready`

Sent once at boot, after the PCA9685 is initialized and all joints are
parked at their neutral (90°) angle.

```json
{"event": "ready", "num_joints": 5, "num_servo_channels": 6}
```

### ESP32 -> PC: `ack`

Confirms a command was accepted and (for `move`) that motion has started.

```json
{"event": "ack", "cmd": "move"}
```

### ESP32 -> PC: `pong`

Reply to `ping`.

### ESP32 -> PC: `error`

Sent when a command couldn't be parsed or was invalid (e.g. wrong number of
angles, or malformed JSON).

```json
{"event": "error", "message": "angles array must have NUM_JOINTS entries"}
```

## Design notes

- The PC always waits for an `ack` on the arm link before sending the next
  `move` in a sequence (see `chess_arm.main._execute_arm_move`), so motion
  happens one waypoint at a time rather than queuing up on the ESP32.
- Board-state updates are push-based (sent only on change) rather than
  polled, since a full 8x8 matrix scan already runs continuously on a
  50 ms tick (`SCAN_INTERVAL_MS` in the board's `config.h`).
- Using two separate serial links instead of multiplexing both boards over
  one connection means a malformed line or a reset on one board can never
  corrupt or stall traffic to the other -- see `docs/architecture.md` for
  the full rationale.
