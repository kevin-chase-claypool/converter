# Pico 2 dual-sensor calibration DAQ

Native Raspberry Pi Pico SDK firmware for the **Raspberry Pi Pico 2**. It does
not use Arduino and it does not command the Pro Micro or the DRV8833.

The Pico owns both raw sensor channels and their monotonic timestamps during a
supervised force-calibration run:

| Pico 2 pin | Function |
|---|---|
| GP2 | CS1238 #1 SCK |
| GP3 | CS1238 #1 DT/DRDY/DOUT |
| GP26 / ADC0 | INA101KU board `OUT`, through 1 kOhm only after the output has been verified within 0-3.3 V |
| GP14 | Temporary Pro Micro `MOTION_ACTIVE` marker input |
| GP15 | Latching DAQ ON/OFF switch to Pico GND; internal pull-up |

The CS1238 configuration is channel A, gain 128, external reference, and
640 SPS. One signed 24-bit CS1238 conversion and one raw 12-bit ADC0 code are
reported per record. It performs no tare, scaling, calibration, or moving
average.

## Build

Install the Raspberry Pi Pico SDK and the ARM GNU toolchain, then set
`PICO_SDK_PATH` to the SDK checkout. From this directory in PowerShell:

```powershell
cmake -S . -B build -DPICO_BOARD=pico2
cmake --build build
```

Copy `build/pico2_dual_sensor_daq.uf2` to the Pico 2's `RPI-RP2` USB boot
drive. The normal firmware USB connection appears as a CDC serial port.

## USB CDC protocol

The firmware writes `READY` after it configures the CS1238. A physical switch
closure starts a run; opening it stops the run. The switch is also an enable
for USB `START`, so a disconnected/open switch cannot start an acquisition.
USB commands are newline-terminated `START`, `STOP`, and `STATUS`.

During a run, the stream is deliberately raw:

```text
TEST_START,source=switch,monotonic_origin_us=...
SAMPLES_HEADER,toolhead_time_us,toolhead_cs1238_raw,reference_time_us,reference_adc_raw
EVENTS_HEADER,pico_time_us,event,marker_level
SAMPLE,0,5823412,7,1247
EVENT,1550,motion_start,1
SAMPLE,1563,5825518,1569,1251
TEST_STOP,reason=daq_switch_off,samples=...,marker_overflow=0
```

`toolhead_time_us`, `reference_time_us`, and event times are relative to the
Pico's `TEST_START` monotonic origin. A future Windows logger creates separate
CSV files by removing the `SAMPLE,` or `EVENT,` record prefix; Windows receipt
time is metadata only, never the sensor clock.

Do not start an unattended actuator test: retain the physical toolhead power
cutoff/E-stop and make only supervised, bounded Pro Micro moves.
