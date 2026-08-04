#pragma once

// ---------------------------------------------------------------------------
// General
// ---------------------------------------------------------------------------
#define SERIAL_BAUD 115200
#define JSON_DOC_SIZE 512

// ---------------------------------------------------------------------------
// Reed switch matrix (8x8 board = 64 squares, wired as a row/column matrix
// to avoid using 64 GPIOs). Each row is driven LOW one at a time while all
// columns are read with pull-ups; a closed reed switch pulls its column LOW.
// Add a diode in series with each switch if you see ghosting on multi-square
// reads.
//
// GPIO34/35/36/39 are input-only on the ESP32 and have NO internal pull-up
// resistor, so they are used here as columns with an external 10k pull-up
// to 3V3 required on each. GPIO0/2/12 (boot strapping) and GPIO1/3 (UART0,
// used by USB serial to the PC) are intentionally left free.
//
// TODO: confirm these GPIOs against your actual wiring before flashing.
// ---------------------------------------------------------------------------
constexpr uint8_t BOARD_SIZE = 8;
constexpr uint8_t ROW_PINS[BOARD_SIZE] = {4, 5, 13, 14, 16, 17, 18, 19};
constexpr uint8_t COL_PINS[BOARD_SIZE] = {34, 35, 36, 39, 21, 22, 23, 25};

// ---------------------------------------------------------------------------
// Arm servos. NUM_SERVOS and SERVO_PINS are the only things you need to
// touch to add/remove joints (e.g. a 5th axis, or swap the gripper for an
// electromagnet driven from a spare digital pin).
//
// TODO: set the real joint count/pins once the arm's DOF is finalized.
// ---------------------------------------------------------------------------
constexpr uint8_t NUM_SERVOS = 5;  // base, shoulder, elbow, wrist, gripper
constexpr uint8_t SERVO_PINS[NUM_SERVOS] = {15, 26, 27, 32, 33};

constexpr uint16_t SERVO_MIN_US = 500;   // 0 deg pulse width
constexpr uint16_t SERVO_MAX_US = 2500;  // 180 deg pulse width

// How often (ms) the reed matrix is scanned.
constexpr uint16_t SCAN_INTERVAL_MS = 50;
