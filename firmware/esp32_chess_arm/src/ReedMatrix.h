#pragma once

#include <Arduino.h>

#include "config.h"

// Scans the row/column reed-switch matrix under the board and keeps the last
// known occupancy state (true = square occupied). Call scan() from loop();
// it returns true only on the tick where the state actually changed, so the
// caller can decide when it's worth sending an update to the PC.
class ReedMatrix {
 public:
  void begin();
  bool scan();
  bool at(uint8_t row, uint8_t col) const;

  // 64-char string of '0'/'1', row-major (row * BOARD_SIZE + col).
  // Mapping this to algebraic squares (a1, e4, ...) is left to the PC side,
  // since it depends on how the board was physically wired/oriented.
  String toStateString() const;

 private:
  bool state_[BOARD_SIZE][BOARD_SIZE] = {};
};
