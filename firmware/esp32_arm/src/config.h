#pragma once

// ---------------------------------------------------------------------------
// General
// ---------------------------------------------------------------------------
#define SERIAL_BAUD 115200
#define JSON_DOC_SIZE 512

// ---------------------------------------------------------------------------
// Servos, driven through a PCA9685 16-channel PWM driver over I2C instead of
// directly from ESP32 GPIOs. Reasons:
//   - 6 MG996R servos can draw several amps combined (stall current alone is
//     well over 1A each); the PCA9685 only carries the PWM *signal*, so the
//     servos' 5-6V power rail (Buslinker + terminal blocks, see
//     docs/wiring.md) never touches the ESP32 at all.
//   - The PCA9685 generates all 6 channels itself in hardware and only needs
//     2 GPIOs (SDA/SCL), instead of juggling 6 separate PWM-capable pins.
//
// TODO: confirm the I2C address/pins against your actual wiring before
// flashing (0x40 is the PCA9685's default with all ADDR pins unbridged).
// ---------------------------------------------------------------------------
// Named ARM_PCA9685_ADDRESS (not PCA9685_I2C_ADDRESS) because the Adafruit
// driver library already #defines that name -- colliding with it breaks
// the build with a cryptic "expected unqualified-id" error.
constexpr uint8_t ARM_PCA9685_ADDRESS = 0x40;
constexpr int I2C_SDA_PIN = 21;  // ESP32 default Wire pins
constexpr int I2C_SCL_PIN = 22;
constexpr float PCA9685_PWM_FREQ_HZ = 50.0f;  // standard analog-servo rate

// ---------------------------------------------------------------------------
// Joint <-> PCA9685 channel mapping.
//
// The arm has 4 degrees of freedom (base, shoulder, elbow, wrist) plus the
// gripper, but the shoulder joint (M2 in the BOM) is driven by *two*
// MG996R servos in parallel for extra torque on the heaviest joint. So
// there are 5 logical joints the PC reasons about -- and that's exactly
// what the `move` command's `angles` array carries, see docs/protocol.md --
// but 6 physical PCA9685 channels. This firmware is the only place that
// knows about that 5-to-6 split; everything upstream (move planning,
// calibration) stays in clean per-joint terms.
// ---------------------------------------------------------------------------
constexpr uint8_t NUM_JOINTS = 5;  // base, shoulder, elbow, wrist, gripper
constexpr uint8_t NUM_SERVO_CHANNELS = 6;
constexpr uint8_t NO_CHANNEL = 255;

// Each joint maps to 1 or 2 PCA9685 channels (NO_CHANNEL = unused second slot).
// clang-format off
constexpr uint8_t JOINT_CHANNELS[NUM_JOINTS][2] = {
    {0, NO_CHANNEL},  // base     (M1, 1 servo)
    {1, 2},           // shoulder (M2, 2 servos in parallel for torque)
    {3, NO_CHANNEL},  // elbow    (M3, 1 servo)
    {4, NO_CHANNEL},  // wrist    (M4, 1 servo)
    {5, NO_CHANNEL},  // gripper  (M5, 1 servo)
};
// clang-format on

constexpr uint16_t SERVO_MIN_US = 500;   // 0 deg pulse width
constexpr uint16_t SERVO_MAX_US = 2500;  // 180 deg pulse width
