#include "ArmController.h"

void ArmController::begin() {
  for (uint8_t i = 0; i < NUM_SERVOS; i++) {
    servos_[i].setPeriodHertz(50);
    servos_[i].attach(SERVO_PINS[i], SERVO_MIN_US, SERVO_MAX_US);
    startAngles_[i] = targetAngles_[i] = 90.0f;  // assume neutral pose at boot
    servos_[i].write(90);
  }
}

void ArmController::moveTo(const float targetAngles[NUM_SERVOS], uint16_t durationMs) {
  for (uint8_t i = 0; i < NUM_SERVOS; i++) {
    startAngles_[i] = servos_[i].read();
    targetAngles_[i] = targetAngles[i];
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

  for (uint8_t i = 0; i < NUM_SERVOS; i++) {
    float angle = startAngles_[i] + (targetAngles_[i] - startAngles_[i]) * t;
    servos_[i].write(static_cast<int>(angle));
  }

  if (t >= 1.0f) {
    moving_ = false;
  }
  return moving_;
}
