# Serial protocol

The ESP32 and the PC talk over USB serial at **115200 baud** using
newline-delimited JSON: every message, in either direction, is a single
JSON object followed by `\n`.

The ESP32 is intentionally "dumb": it only reports raw board occupancy and
executes joint-angle commands. All chess rules and motion planning live on
the PC (`software/chess_arm/`).

## PC -> ESP32

### `move`

Moves every servo to the given angles, interpolating smoothly over
`duration_ms`.

```json
{"cmd": "move", "angles": [90, 45, 120, 90, 40], "duration_ms": 800}
```

- `angles` has exactly `NUM_SERVOS` entries (default 5: base, shoulder,
  elbow, wrist, gripper — see `firmware/esp32_chess_arm/src/config.h`),
  in degrees.
- `duration_ms` is optional, default `800`.

### `ping`

```json
{"cmd": "ping"}
```

Used as a liveness check; the ESP32 replies with a `pong` event.

## ESP32 -> PC

### `ready`

Sent once at boot, after the reed matrix and servos are initialized.

```json
{"event": "ready", "board_size": 8, "num_servos": 5}
```

### `board`

Sent whenever the reed-switch matrix scan detects a change. `state` is a
64-character string of `'0'`/`'1'`, indexed `row * board_size + col`
(row-major). Mapping `(row, col)` to algebraic squares (a1, e4, ...) is a
PC-side concern — see `chess_arm.board_state.default_square_order` — since
it depends on how the board was physically wired.

```json
{"event": "board", "state": "0000000000000000000000000000000000000000000000000000000000000000"}
```

(real strings are 64 characters; shortened here for readability)

### `ack`

Confirms a command was accepted and (for `move`) that motion has started.

```json
{"event": "ack", "cmd": "move"}
```

### `pong`

Reply to `ping`.

### `error`

Sent when a command couldn't be parsed or was invalid (e.g. wrong number of
angles, or malformed JSON).

```json
{"event": "error", "message": "angles array must have NUM_SERVOS entries"}
```

## Design notes

- The PC always waits for an `ack` before sending the next `move` in a
  sequence (see `chess_arm.main._execute_arm_move`), so motion happens one
  waypoint at a time rather than queuing up on the ESP32.
- Board-state updates are push-based (sent only on change) rather than
  polled, since a full 8x8 matrix scan already runs continuously on a
  50 ms tick (`SCAN_INTERVAL_MS` in `config.h`).
