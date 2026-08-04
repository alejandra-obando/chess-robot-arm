# Wiring

> The pin assignments below are the firmware's defaults
> (`firmware/esp32_board/src/config.h` and `firmware/esp32_arm/src/config.h`).
> Treat them as a starting point and update the relevant `config.h` to match
> your actual build -- this file documents *why* those particular pins were
> picked, so you can make the same kind of tradeoff if you change them.

There are two independent ESP32s, each with its own USB cable to the PC.
They never talk to each other.

## ESP32 #2 -- board (reed matrix + mux)

### Reed switch matrix (8x8 board)

64 reed switches would need 64 GPIOs if wired individually, which an ESP32
doesn't have. Instead they're wired as an 8x8 row/column matrix (same idea
as a keyboard matrix): one lead of every switch in a row ties to that row's
line, the other lead of every switch in a column ties to that column's
line. Scanning drives one row LOW at a time and reads all 8 columns, so a
closed switch pulls its column LOW only while its row is active.

Rows are driven directly from 8 GPIOs. Columns are **not** wired to 8
separate GPIOs -- they go through the 16-channel analog multiplexer
(CD74HC4067) instead, which reads all 8 (up to 16) columns through just 5
ESP32 pins: 4 binary-select lines plus 1 shared signal line.

| Signal | GPIOs |
|---|---|
| Rows (output, driven LOW one at a time) | 4, 5, 13, 14, 16, 17, 18, 19 |
| Mux select S0-S3 (output, binary-encode the channel 0-15) | 25, 26, 27, 32 |
| Mux SIG (input, pulled up, read while a row + mux channel are active) | 33 |

Notes:

- The mux's on-resistance (tens of ohms) is low enough that the ESP32's
  **internal `INPUT_PULLUP`** works fine through it on the SIG line -- no
  external pull-up resistor needed, unlike a bare GPIO34-39 hookup.
- Only 8 of the mux's 16 channels are used (`COL_MUX_CHANNELS` in
  `config.h`); the other 8 are free for a bigger board or extra digital
  sensors later without adding wiring.
- **GPIO0, 2, 12 are boot-strapping pins** and **GPIO1/3 are UART0**
  (the same lines used for USB serial to the PC) -- all intentionally left
  unused so flashing and the PC link stay reliable.
- If you see "ghost" readings (a square reporting occupied when it isn't,
  because current sneaks back through another closed switch in the same
  row/column), add a diode in series with each reed switch.

## ESP32 #1 -- arm (PCA9685 + servos)

### Servos (via PCA9685, I2C)

The arm has **4 degrees of freedom + a gripper** (5 logical joints), driven
by **6 MG996R servos** total -- the shoulder joint uses two servos in
parallel for extra torque, since it carries the weight of every joint above
it.

| Joint | PCA9685 channel(s) | Servo(s) in BOM |
|---|---|---|
| Base (rotation) | 0 | M1 |
| Shoulder (1st articulation) | 1, 2 (mirrored) | M2 (x2) |
| Elbow (2nd articulation) | 3 | M3 |
| Wrist (3rd articulation) | 4 | M4 |
| Gripper | 5 | M5 |

| Signal | GPIO |
|---|---|
| I2C SDA (to PCA9685) | 21 |
| I2C SCL (to PCA9685) | 22 |

Servos don't connect to the ESP32 at all -- they connect to the PCA9685's
per-channel headers, which carry the PWM signal plus the servos' own power
rail pass-through pin.

**Why a PCA9685 instead of direct GPIO PWM:** 6 MG996R servos moving at once
can pull several amps combined, and a stalled servo alone can spike over
1A. Running that current anywhere near the ESP32's signal pins is asking for
brownouts and noisy readings. The PCA9685 only carries the low-current PWM
*signal*; it has its own separate `V+` terminal for the servo power rail,
so the two never share a path back to the ESP32.

`NUM_JOINTS`, `NUM_SERVO_CHANNELS` and `JOINT_CHANNELS` in `config.h` are
what to touch if the arm's DOF count or the shoulder's servo pairing ever
changes.

## Power distribution (servo rail)

- **Buslinker v2.5** -- splits the external 5-6V supply out to the
  PCA9685's `V+` terminal and, from there, to all 6 servo power leads,
  keeping that whole rail separate from the ESP32s' own USB power.
- **100µF 16V capacitor** across the servo rail, as close to the PCA9685's
  `V+`/`GND` terminals as practical -- absorbs the current spikes from
  multiple servos starting/stopping at once, which otherwise show up as
  brownouts or the PCA9685 resetting mid-motion.
- **Blue terminal blocks** -- screw-terminal connections for the incoming
  supply and the distributed rail, instead of soldering/twisting the power
  wiring directly (easier to service, less likely to short).
- **Red/black power cable** -- carries the servo supply; keep it separate
  from the ESP32s' USB cables and reed-switch matrix wiring to avoid
  coupling PWM/switching noise into the low-current signal lines.

Ground everything together: both ESP32s' GND, the PCA9685's logic GND, and
the servo rail's GND must share a common reference, even though the servo
rail's power comes from a separate supply than the ESP32s' USB power.

## TODO before flashing

- [ ] Confirm the reed switch matrix and mux wiring on ESP32 #2 matches
      `ROW_PINS`/`MUX_SELECT_PINS`/`MUX_SIGNAL_PIN`/`COL_MUX_CHANNELS`.
- [ ] Confirm the PCA9685 I2C address/pins and channel-to-joint mapping on
      ESP32 #1 match `ARM_PCA9685_ADDRESS`/`I2C_SDA_PIN`/`I2C_SCL_PIN`/
      `JOINT_CHANNELS`.
- [ ] Verify the servo rail's capacitor and terminal blocks are rated for
      your supply voltage/current before powering up all 6 servos at once.
