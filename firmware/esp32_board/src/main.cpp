// ESP32 #2 firmware -- chessboard sensing.
//
// Deliberately "dumb"; all chess logic lives on the PC (see
// software/chess_arm). This board's only job is scanning the 8x8
// reed-switch matrix (rows direct, columns through a 16-channel analog
// mux -- see config.h) and reporting occupancy changes over USB serial.
// Arm control is a separate ESP32 -- see firmware/esp32_arm -- with its own
// USB-serial link to the PC; the two boards don't talk to each other.
//
// Communication is newline-delimited JSON over USB serial -- see
// docs/protocol.md.

#include <Arduino.h>
#include <ArduinoJson.h>

#include "Protocol.h"
#include "ReedMatrix.h"
#include "config.h"

namespace {
ReedMatrix reedMatrix;
uint32_t lastScanMs = 0;
}  // namespace

void handleCommand(const JsonDocument& cmd) {
  const char* type = cmd["cmd"] | "";

  if (strcmp(type, "ping") == 0) {
    protocol::sendPong();
  } else {
    protocol::sendError("unknown cmd");
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  reedMatrix.begin();
  protocol::sendReady();
}

void loop() {
  JsonDocument cmd;
  if (protocol::pollCommand(cmd)) {
    handleCommand(cmd);
  }

  uint32_t now = millis();
  if (now - lastScanMs >= SCAN_INTERVAL_MS) {
    lastScanMs = now;
    if (reedMatrix.scan()) {
      protocol::sendBoardState(reedMatrix.toStateString());
    }
  }
}
