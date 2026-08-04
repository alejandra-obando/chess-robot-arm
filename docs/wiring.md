# Wiring

> The pin assignments below are the firmware's defaults
> (`firmware/esp32_chess_arm/src/config.h`). Treat them as a starting point
> and update `config.h` to match your actual build — this file documents
> *why* those particular pins were picked, so you can make the same kind of
> tradeoff if you change them.

## Reed switch matrix (8x8 board)

64 reed switches would need 64 GPIOs if wired individually, which an ESP32
doesn't have. Instead they're wired as an 8x8 row/column matrix (same idea
as a keyboard matrix): one lead of every switch in a row ties to that row's
line, the other lead of every switch in a column ties to that column's
line. Scanning drives one row LOW at a time and reads all 8 columns, so a
closed switch pulls its column LOW only while its row is active.

| Signal | GPIOs |
|---|---|
| Rows (output, driven LOW one at a time) | 4, 5, 13, 14, 16, 17, 18, 19 |
| Columns (input, pulled up, read while a row is active) | 34, 35, 36, 39, 21, 22, 23, 25 |

Notes:

- **GPIO34/35/36/39 are input-only** on the ESP32 and have **no internal
  pull-up**. They're used as columns here, but each needs an **external
  10k resistor to 3V3**. The other four columns (21/22/23/25) use the
  ESP32's internal `INPUT_PULLUP`.
- **GPIO0, 2, 12 are boot-strapping pins** and **GPIO1/3 are UART0**
  (the same lines used for USB serial to the PC) — all intentionally left
  unused so flashing and the PC link stay reliable.
- If you see "ghost" readings (a square reporting occupied when it isn't,
  because current sneaks back through another closed switch in the same
  row/column), add a diode in series with each reed switch.

## Servos

| Joint | GPIO |
|---|---|
| Base | 15 |
| Shoulder | 26 |
| Elbow | 27 |
| Wrist | 32 |
| Gripper | 33 |

`NUM_SERVOS` and `SERVO_PINS` in `config.h` are the only things to touch if
the arm ends up with a different number of joints (e.g. a turntable base,
or an electromagnet on a spare digital pin instead of a gripper servo).

**Power:** don't power servos from the ESP32's 5V/3V3 regulator — a
stalled servo can draw well over an amp and brown out the board. Use a
separate 5-6V supply sized for however many servos move at once, and tie
its ground to the ESP32's ground.

## TODO before flashing

- [ ] Confirm the arm's final DOF count and update `NUM_SERVOS`/`SERVO_PINS`.
- [ ] Confirm the reed switch matrix wiring matches `ROW_PINS`/`COL_PINS`
      (or update them to match your build).
- [ ] Add the external pull-ups on GPIO34/35/36/39 if using those columns.
- [ ] Fill in a real bill of materials once parts are finalized.
