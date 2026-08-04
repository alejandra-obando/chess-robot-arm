// ESP32 #1 firmware -- robotic arm control.
//
// Deliberately "dumb"; all chess logic lives on the PC (see
// software/chess_arm). This board's only job is driving the arm's 6 servos
// (5 logical joints, see config.h) to whatever angles the PC asks for, via
// a PCA9685 PWM driver over I2C. Board sensing (the reed-switch matrix) is a
// separate ESP32 -- see firmware/esp32_board -- with its own USB-serial link
// to the PC; the two boards don't talk to each other.
//
// Communication is newline-delimited JSON over USB serial -- see
// docs/protocol.md.

#include <Arduino.h>
#include <ArduinoJson.h>

#include "ArmController.h"
#include "Protocol.h"
#include "config.h"

namespace {
ArmController arm;
}  // namespace

void handleCommand(const JsonDocument& cmd) {
  const char* type = cmd["cmd"] | "";

  if (strcmp(type, "move") == 0) {
    JsonArrayConst angles = cmd["angles"];
    if (angles.size() != NUM_JOINTS) {
      protocol::sendError("angles array must have NUM_JOINTS entries");
      return;
    }
    float targets[NUM_JOINTS];
    for (uint8_t i = 0; i < NUM_JOINTS; i++) targets[i] = angles[i].as<float>();

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
  arm.begin();
  protocol::sendReady();
}

void loop() {
  JsonDocument cmd;
  if (protocol::pollCommand(cmd)) {
    handleCommand(cmd);
  }

  arm.update();
}
