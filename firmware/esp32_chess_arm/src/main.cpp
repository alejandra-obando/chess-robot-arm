// ESP32 firmware for the chess-playing robotic arm.
//
// Responsibilities (deliberately "dumb"; all chess logic lives on the PC,
// see software/chess_arm):
//   1. Scan the 8x8 reed-switch matrix under the board and report the
//      occupancy state whenever it changes.
//   2. Drive the arm's servos to whatever angles the PC asks for.
// Communication is newline-delimited JSON over USB serial -- see
// docs/protocol.md.

#include <Arduino.h>
#include <ArduinoJson.h>

#include "ArmController.h"
#include "Protocol.h"
#include "ReedMatrix.h"
#include "config.h"

namespace {
ReedMatrix reedMatrix;
ArmController arm;
uint32_t lastScanMs = 0;
}  // namespace

void handleCommand(const JsonDocument& cmd) {
  const char* type = cmd["cmd"] | "";

  if (strcmp(type, "move") == 0) {
    JsonArrayConst angles = cmd["angles"];
    if (angles.size() != NUM_SERVOS) {
      protocol::sendError("angles array must have NUM_SERVOS entries");
      return;
    }
    float targets[NUM_SERVOS];
    for (uint8_t i = 0; i < NUM_SERVOS; i++) targets[i] = angles[i].as<float>();

    uint16_t duration = cmd["duration_ms"] | 800;
    arm.moveTo(targets, duration);
    protocol::sendAck("move");

  } else if (strcmp(type, "ping") == 0) {
    protocol::sendPong();

  } else {
    protocol::sendError("unknown cmd");
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  reedMatrix.begin();
  arm.begin();
  protocol::sendReady();
}

void loop() {
  JsonDocument cmd;
  if (protocol::pollCommand(cmd)) {
    handleCommand(cmd);
  }

  arm.update();

  uint32_t now = millis();
  if (now - lastScanMs >= SCAN_INTERVAL_MS) {
    lastScanMs = now;
    if (reedMatrix.scan()) {
      protocol::sendBoardState(reedMatrix.toStateString());
    }
  }
}
