#pragma once

#include <Arduino.h>
#include <ArduinoJson.h>

#include "config.h"

// Newline-delimited JSON protocol between the ESP32 and the PC.
// Full spec lives in docs/protocol.md at the repo root.
namespace protocol {

void sendReady();
void sendBoardState(const String& stateString);
void sendAck(const char* cmd);
void sendPong();
void sendError(const char* message);

// Reads at most one complete line from Serial (non-blocking). Returns true
// and fills `out` if a full JSON command was received and parsed.
bool pollCommand(JsonDocument& out);

}  // namespace protocol
