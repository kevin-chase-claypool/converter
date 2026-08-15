# Lab Note: 2026-08-14 - E-09 TMAG5273 Intended-Wiring Verification

## Objective

Verify that the toolhead TMAG5273 is online through its final Qwiic/I2C wiring,
has stable stationary field readings, and responds strongly to the intended
magnet.

## Setup

- Controller: SparkFun Pro Micro RP2350.
- Sensor: SparkFun TMAG5273 Qwiic.
- I2C: Qwiic `GPIO16`/SDA to TMAG SDA; Qwiic `GPIO17`/SCL to TMAG SCL;
  Qwiic 3.3 V/GND supplies the sensor.
- Telemetry: DSD TECH SH-U09C2 at 3.3 V logic; adapter GND to `TOOL_GND`, RXD
  to GP20, TXD to GP21; adapter VCC disconnected.
- Power: upload over USB-C with local 6 V off, then remove USB-C and operate
  from local 6 V.
- Safety: E-09 never enables the DRV8833 or N20 motor.

## Exact firmware

```text
firmware/pen_pressure/e09_tmag5273_verification/e09_tmag5273_verification.ino
SHA-256: C32795A9FF940B2FBF1744B5FA07F6A1DC2B546F627945C88F6C479D9E473B06
FQBN: rp2040:rp2040:sparkfun_promicrorp2350
```

Append the source SHA-256 and actual UART results after execution.

## Procedure

1. Upload the E-09 sketch with local 6 V off, then disconnect Pro Micro USB-C.
2. Open the service UART at 115200 and apply local 6 V.
3. Confirm `UART ready...`, then send `i` and confirm `TMAG5273 online at I2C
   address 0x22.` The deferred initialization keeps UART diagnostics available
   even if a Qwiic/I2C fault prevents sensor startup.
4. With the intended magnet held still at its normal far/reference position,
   send `r` and record the stability result.
5. Send `p` and record the vector/magnitude.
6. Bring the intended magnet near the sensor without touching it, send `p`,
   and record the changed vector/magnitude.
7. Move the magnet away and repeat `p`; confirm the reading returns toward the
   original reference value.

## Results

The revised E-09 sketch established the GP20/GP21 service UART and printed:

```text
E-09 TMAG5273 intended-wiring test
UART ready. Send i to initialize Qwiic I2C/TMAG5273.
E-09: i=initialize p=one vector r=20-sample stability ?=help
```

After command `i`, it printed the following and did not continue:

```text
Initializing Qwiic I2C on SDA GPIO17 / SCL GPIO16...
```

This is an E-09 I2C-startup failure, not a UART failure. Subsequent powered
measurements confirmed sensor 3V3, SDA, and SCL were all near 3.3 V, ruling out
an unpowered sensor or a line held low. The actual fault was the prior reversed
SDA/SCL assignment: the installed Arduino RP2350 board definition and RP2350
I2C0 function mapping require GP16 as SDA and GP17 as SCL. Swap only those two
signal conductors and retry with the revised E-09 sketch.

After the SDA/SCL swap, `i` completed and the TMAG5273 was online. A stationary
20-sample window reported `mean_magnitude_mT=13.94` with a 0.28 mT
peak-to-peak span, demonstrating stable field acquisition. A subsequent vector
report was `mag_mT=[0.20,0.08,0.20]` with a 0.29 mT calculated magnitude. The
large difference means the far/reference condition was not yet controlled
between the two commands, so collect repeated vectors at one fixed position
before selecting a threshold. The earlier `0x35` success-message text was a
reporting typo; the SparkFun library's default initial address is `0x22`, and
the successful device-ID transaction remains valid.

The controlled retry placed the TMAG directly over the intended magnet and did
not move the sensor, bed, or magnet between readings:

```text
mag_mT=[-0.08,-2.77,-7.11] magnitude_mT=7.63 temp_C=30.3
mag_mT=[0.16,-2.62,-7.07] magnitude_mT=7.54 temp_C=30.0
mag_mT=[0.16,-2.70,-7.07] magnitude_mT=7.57 temp_C=30.3
E-09 stability result
samples=20
mean_magnitude_mT=7.51
min_magnitude_mT=7.39
max_magnitude_mT=7.66
peak_to_peak_mT=0.28
mag_mT=[0.16,-2.66,-7.11] magnitude_mT=7.59 temp_C=30.0
```

The one-shot readings (7.54-7.63 mT) match the 7.51 mT stability-window mean,
confirming stable vector acquisition at that fixed near-magnet position. The
earlier mismatch was caused by uncontrolled position between commands, not a
sensor or firmware defect. Record a controlled far-reference value and return
value next before selecting a threshold.

The controlled far/reference position reported:

```text
mag_mT=[0.12,0.23,0.08] magnitude_mT=0.27 temp_C=29.5
E-09 stability result
samples=20
mean_magnitude_mT=0.24
min_magnitude_mT=0.12
max_magnitude_mT=0.37
peak_to_peak_mT=0.25
mag_mT=[0.00,0.08,0.12] magnitude_mT=0.14 temp_C=30.0
```

After returning directly over the same intended magnet, the sensor reported:

```text
mag_mT=[-0.62,-2.58,-6.95] magnitude_mT=7.44 temp_C=30.0
```

E-09 **passed**. Near field returned to 7.44 mT, consistent with the 7.51 mT
near-position mean, while the far mean was 0.24 mT. The approximately 7.3 mT
separation is far larger than either stationary span (0.25-0.28 mT). A
conservative initial magnitude threshold is 3.5 mT, with about 1.0 mT
hysteresis; final scan geometry still determines the production threshold.

## Pass criteria

- I2C device is found at the expected address.
- Stationary 20-sample magnitude span is small relative to the far-to-near
  magnetic change.
- The field vector/magnitude changes predictably near the intended magnet and
  returns after it is moved away.

## Follow-up

With power off, confirm GP16 to SDA, GP17 to SCL, 3V3 to sensor 3V3, and
`TOOL_GND` to sensor GND. Confirm no short between SDA/SCL and ground or each
other. With local 6 V on, measure sensor 3V3-to-GND (about 3.3 V) and both
idle SDA-to-GND and SCL-to-GND (normally near 3.3 V due to pullups). After the
bus is healthy, use the measured far/reference and near-magnet values to choose
threshold and hysteresis during the later A_HOME/E-18 integration test.
