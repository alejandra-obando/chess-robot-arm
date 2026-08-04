#pragma once

#include <ESP32Servo.h>

#include "config.h"

// Thin wrapper around NUM_SERVOS servos. All motion is done as a smooth,
// non-blocking interpolation between the current and target angles so the
// arm doesn't snap between waypoints -- both for the mechanics' sake and
// because it looks a lot better on camera.
class ArmController {
 public:
  void begin();

  // Starts moving toward target angles (degrees, one per servo) over
  // durationMs. Call update() regularly from loop() to advance the motion.
  void moveTo(const float targetAngles[NUM_SERVOS], uint16_t durationMs);

  // Advances any in-progress motion. Returns true while still moving.
  bool update();

  bool isMoving() const { return moving_; }

 private:
  Servo servos_[NUM_SERVOS];
  float startAngles_[NUM_SERVOS] = {};
  float targetAngles_[NUM_SERVOS] = {};
  uint32_t motionStartMs_ = 0;
  uint16_t motionDurationMs_ = 0;
  bool moving_ = false;
};
