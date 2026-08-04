#include "ReedMatrix.h"

void ReedMatrix::begin() {
  for (uint8_t r = 0; r < BOARD_SIZE; r++) {
    pinMode(ROW_PINS[r], OUTPUT);
    digitalWrite(ROW_PINS[r], HIGH);  // idle high, driven low while scanned
  }
  for (uint8_t s = 0; s < 4; s++) {
    pinMode(MUX_SELECT_PINS[s], OUTPUT);
  }
  // The mux's on-resistance is low enough that the ESP32's internal
  // pull-up works fine through it -- no external resistor needed.
  pinMode(MUX_SIGNAL_PIN, INPUT_PULLUP);
}

void ReedMatrix::selectMuxChannel(uint8_t channel) const {
  for (uint8_t s = 0; s < 4; s++) {
    digitalWrite(MUX_SELECT_PINS[s], (channel >> s) & 0x01);
  }
  delayMicroseconds(5);  // let the mux's analog switches settle
}

bool ReedMatrix::readColumn(uint8_t col) const {
  selectMuxChannel(COL_MUX_CHANNELS[col]);
  // Closed reed switch pulls the shared SIG line LOW when its row is
  // driven LOW and its column is the one currently selected on the mux.
  return digitalRead(MUX_SIGNAL_PIN) == LOW;
}

bool ReedMatrix::scan() {
  bool changed = false;

  for (uint8_t r = 0; r < BOARD_SIZE; r++) {
    digitalWrite(ROW_PINS[r], LOW);
    delayMicroseconds(20);  // let the line settle before sampling

    for (uint8_t c = 0; c < BOARD_SIZE; c++) {
      bool occupied = readColumn(c);
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
