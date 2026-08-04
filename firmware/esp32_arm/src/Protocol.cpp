#include "Protocol.h"

namespace protocol {

namespace {
String lineBuffer;
}  // namespace

void sendReady() {
  JsonDocument doc;
  doc["event"] = "ready";
  doc["num_joints"] = NUM_JOINTS;
  doc["num_servo_channels"] = NUM_SERVO_CHANNELS;
  serializeJson(doc, Serial);
  Serial.println();
}

void sendAck(const char* cmd) {
  JsonDocument doc;
  doc["event"] = "ack";
  doc["cmd"] = cmd;
  serializeJson(doc, Serial);
  Serial.println();
}

void sendPong() {
  JsonDocument doc;
  doc["event"] = "pong";
  serializeJson(doc, Serial);
  Serial.println();
}

void sendError(const char* message) {
  JsonDocument doc;
  doc["event"] = "error";
  doc["message"] = message;
  serializeJson(doc, Serial);
  Serial.println();
}

bool pollCommand(JsonDocument& out) {
  while (Serial.available() > 0) {
    char c = static_cast<char>(Serial.read());
    if (c == '\n') {
      if (lineBuffer.length() == 0) continue;

      DeserializationError err = deserializeJson(out, lineBuffer);
      lineBuffer = "";
      if (err) {
        sendError(err.c_str());
        return false;
      }
      return true;
    }
    if (c != '\r') {
      lineBuffer += c;
      if (lineBuffer.length() > JSON_DOC_SIZE) {
        lineBuffer = "";  // guard against a runaway/garbled line
      }
    }
  }
  return false;
}

}  // namespace protocol
