# Pico 2 dual-sensor calibration DAQ

Arduino-Pico firmware for the **Raspberry Pi Pico 2**. It does not require an
Arduino board and it does not command the Pro Micro or the DRV8833.

The Pico owns both raw sensor channels and their monotonic timestamps during a
supervised force-calibration run:

| Pico 2 pin | Function |
|---|---|
| GP2 | CS1238 #1 SCK |
| GP3 | CS1238 #1 DT/DRDY/DOUT |
| GP26 / ADC0 | INA101KU board `OUT`, through 1 kOhm only after the output has been verified within 0-3.3 V |
| GP15 | Pro Micro GP0 DAQ-gate input; internal pull-up |

The CS1238 configuration is channel A, gain 128, external reference, and
640 SPS. One signed 24-bit CS1238 conversion and one raw 12-bit ADC0 code are
reported per record. It performs no tare, scaling, calibration, or moving
average.

## Upload

In Arduino IDE, select **Raspberry Pi Pico 2**, open `pico2_daq.ino`, and
upload. Its normal USB connection appears as a CDC serial port.

## USB CDC protocol

The firmware writes `READY` after it configures the CS1238. Pro Micro GP0 LOW
starts a run and GP0 HIGH stops it through Pico GP15. GP0 defaults HIGH at
Pro Micro reset, so a reset safely stops capture. USB `START`, `STOP`, and
`STATUS` remain available for bench diagnosis, but normal runs use the GP0
gate and the PC logger does not start the Pico directly.

During a run, the stream is deliberately raw:

```text
TEST_START,source=gp0_gate,monotonic_origin_us=...
SAMPLES_HEADER,toolhead_time_us,toolhead_cs1238_raw,reference_time_us,reference_adc_raw
SAMPLE,0,5823412,7,1247
SAMPLE,1563,5825518,1569,1251
TEST_STOP,reason=daq_gate_off,samples=...
```

`toolhead_time_us` and `reference_time_us` are relative to the Pico's
`TEST_START` monotonic origin. The Windows logger creates `samples.csv` by
removing the `SAMPLE,` prefix and saves lifecycle records separately; Windows
receipt time is metadata only, never the sensor clock.

Do not start an unattended actuator test: retain the physical toolhead power
cutoff/E-stop and make only supervised, bounded Pro Micro moves.
