#include "ReedMatrix.h"

void ReedMatrix::begin() {
  for (uint8_t r = 0; r < BOARD_SIZE; r++) {
    pinMode(ROW_PINS[r], OUTPUT);
    digitalWrite(ROW_PINS[r], HIGH);  // idle high, driven low while scanned
  }
  for (uint8_t c = 0; c < BOARD_SIZE; c++) {
    // Note: GPIO34-39 have no internal pull-up (see config.h) and need an
    // external 10k resistor to 3V3 on those columns.
    pinMode(COL_PINS[c], INPUT_PULLUP);
  }
}

bool ReedMatrix::scan() {
  bool changed = false;

  for (uint8_t r = 0; r < BOARD_SIZE; r++) {
    digitalWrite(ROW_PINS[r], LOW);
    delayMicroseconds(20);  // let the line settle before sampling

    for (uint8_t c = 0; c < BOARD_SIZE; c++) {
      // Closed reed switch pulls the column LOW when its row is driven LOW.
      bool occupied = (digitalRead(COL_PINS[c]) == LOW);
      if (occupied != state_[r][c]) {
        state_[r][c] = occupied;
        changed = true;
      }
    }

    digitalWrite(ROW_PINS[r], HIGH);
  }

  return changed;
}

bool ReedMatrix::at(uint8_t row, uint8_t col) const { return state_[row][col]; }

String ReedMatrix::toStateString() const {
  String out;
  out.reserve(BOARD_SIZE * BOARD_SIZE);
  for (uint8_t r = 0; r < BOARD_SIZE; r++) {
    for (uint8_t c = 0; c < BOARD_SIZE; c++) {
      out += state_[r][c] ? '1' : '0';
    }
  }
  return out;
}
