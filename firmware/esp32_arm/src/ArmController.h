#pragma once

#include <Adafruit_PWMServoDriver.h>

#include "config.h"

// Drives the arm's 6 physical servos (5 logical joints, see config.h) through
// a PCA9685 PWM driver over I2C. All motion is done as a smooth, non-blocking
// interpolation between the current and target angles so the arm doesn't
// snap between waypoints -- both for the mechanics' sake and because it
// looks a lot better on camera.
class ArmController {
 public:
  void begin();

  // Starts moving toward target angles (degrees, one per logical joint) over
  // durationMs. Call update() regularly from loop() to advance the motion.
  void moveTo(const float targetAngles[NUM_JOINTS], uint16_t durationMs);

  // Advances any in-progress motion. Returns true while still moving.
  bool update();

  bool isMoving() const { return moving_; }

 private:
  void writeJointAngle(uint8_t joint, float angleDeg);

  Adafruit_PWMServoDriver pwm_{ARM_PCA9685_ADDRESS};
  // Unlike a direct-GPIO Servo object, the PCA9685 can't be read back, so
  // the last angle written to each joint is tracked here -- it doubles as
  // the start angle for the next moveTo().
  float lastAngles_[NUM_JOINTS] = {};
  float startAngles_[NUM_JOINTS] = {};
  float targetAngles_[NUM_JOINTS] = {};
  uint32_t motionStartMs_ = 0;
  uint16_t motionDurationMs_ = 0;
  bool moving_ = false;
};
