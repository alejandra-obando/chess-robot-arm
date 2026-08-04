#include "ArmController.h"

#include <Wire.h>

void ArmController::begin() {
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  pwm_.begin();
  pwm_.setPWMFreq(PCA9685_PWM_FREQ_HZ);

  for (uint8_t j = 0; j < NUM_JOINTS; j++) {
    startAngles_[j] = targetAngles_[j] = 90.0f;  // assume neutral pose at boot
    writeJointAngle(j, 90.0f);
  }
}

void ArmController::writeJointAngle(uint8_t joint, float angleDeg) {
  float clamped = angleDeg < 0.0f ? 0.0f : (angleDeg > 180.0f ? 180.0f : angleDeg);
  uint16_t pulseUs = SERVO_MIN_US + static_cast<uint16_t>(
                                         (SERVO_MAX_US - SERVO_MIN_US) * (clamped / 180.0f));

  // Joints with two channels (the shoulder's paired M2 servos) get the same
  // pulse written to both, so they move in lockstep.
  for (uint8_t k = 0; k < 2; k++) {
    uint8_t channel = JOINT_CHANNELS[joint][k];
    if (channel == NO_CHANNEL) continue;
    pwm_.writeMicroseconds(channel, pulseUs);
  }
  lastAngles_[joint] = clamped;
}

void ArmController::moveTo(const float targetAngles[NUM_JOINTS], uint16_t durationMs) {
  for (uint8_t j = 0; j < NUM_JOINTS; j++) {
    startAngles_[j] = lastAngles_[j];
    targetAngles_[j] = targetAngles[j];
  }
  motionStartMs_ = millis();
  motionDurationMs_ = durationMs > 0 ? durationMs : 1;
  moving_ = true;
}

bool ArmController::update() {
  if (!moving_) return false;

  uint32_t elapsed = millis() - motionStartMs_;
  float t = static_cast<float>(elapsed) / static_cast<float>(motionDurationMs_);
  if (t >= 1.0f) t = 1.0f;

  for (uint8_t j = 0; j < NUM_JOINTS; j++) {
    float angle = startAngles_[j] + (targetAngles_[j] - startAngles_[j]) * t;
    writeJointAngle(j, angle);
  }

  if (t >= 1.0f) {
    moving_ = false;
  }
  return moving_;
}
