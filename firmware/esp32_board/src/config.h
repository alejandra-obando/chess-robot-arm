#pragma once

// ---------------------------------------------------------------------------
// General
// ---------------------------------------------------------------------------
#define SERIAL_BAUD 115200
#define JSON_DOC_SIZE 512

// ---------------------------------------------------------------------------
// Reed switch matrix (8x8 board = 64 squares, wired as a row/column matrix
// to avoid needing 64 GPIOs). Each row is driven LOW one at a time; a closed
// reed switch pulls its column LOW while that row is active.
//
// Rows are still driven directly (8 GPIOs), but instead of also wiring 8
// direct column inputs, the columns are read through a single CD74HC4067
// 16-channel analog multiplexer: 4 select lines choose which of its 16
// inputs is connected to the shared SIG pin, which the ESP32 reads with a
// single GPIO. That trades 8 GPIOs for 5 (4 select + 1 signal) and leaves
// 8 of the mux's 16 channels free for a bigger board or extra digital
// sensors later.
//
// GPIO0/2/12 (boot-strapping) and GPIO1/3 (UART0, used by USB serial to the
// PC) are intentionally left free.
//
// TODO: confirm these GPIOs against your actual wiring before flashing.
// ---------------------------------------------------------------------------
constexpr uint8_t BOARD_SIZE = 8;
constexpr uint8_t ROW_PINS[BOARD_SIZE] = {4, 5, 13, 14, 16, 17, 18, 19};

// CD74HC4067 select pins S0..S3 (binary-encode the channel to read, 0-15).
constexpr uint8_t MUX_SELECT_PINS[4] = {25, 26, 27, 32};
// CD74HC4067 SIG pin -- shared input for whichever channel is selected.
// Internal pull-up works fine through the mux's low on-resistance, so no
// external resistor is needed here (unlike a direct GPIO34-39 hookup).
constexpr uint8_t MUX_SIGNAL_PIN = 33;

// Which mux channel (0-15) each of the 8 matrix columns is wired to. Default
// assumes columns are wired to mux channels 0-7 in order, leaving 8-15 free.
constexpr uint8_t COL_MUX_CHANNELS[BOARD_SIZE] = {0, 1, 2, 3, 4, 5, 6, 7};

// How often (ms) the reed matrix is scanned.
constexpr uint16_t SCAN_INTERVAL_MS = 50;
