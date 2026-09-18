# Pico 2 dual-sensor calibration DAQ

## Purpose and boundary

This is a temporary, supervised bench fixture for calibrating the installed
toolhead 300 g load cell while the existing Pro Micro commands controlled
downward pen motion. It replaces the historical HX711/kitchen-scale method.
The Pico replaces only the toolhead bridge's ADC during the test; the Pro
Micro remains the actuator-command controller. It does not enable production
closed-loop force control or alter the E-stop topology.

The Pico 2 reads both channels on one monotonic microsecond time base and
streams raw records through its micro-USB connection to a PC logger. The PC
wall clock identifies a run; Pico timestamps are the measurement time base.

The accompanying wiring diagram is
[`pico2-dual-sensor-daq.html`](pico2-dual-sensor-daq.html).

## Test wiring

| Path | Connection | Status / condition |
|---|---|---|
| Toolhead sensor | Installed 300 g load cell -> CS1238 #1 channel A | Planned. Use the received board's verified `E+`, `E-`, `A+`, and `A-` labels. The load cell must not be connected to an HX711 or Pro Micro ADC at the same time. |
| Toolhead actuation | Existing 6 V toolhead input -> DRV8833 motor rail and S7V8F5 -> regulated 5 V Pro Micro supply | Required for the loaded calibration phase. The Pro Micro commands controlled downward/upward pen motion; do not feed 6 V directly to the Pro Micro. |
| Toolhead commands | Existing USB-to-TTL service adapter -> Pro Micro UART1 `GP20`/`GP21` | Required for the loaded calibration phase. Use the existing documented command interface; this command path is separate from the Pico measurement time base. |
| CS1238 power | Pico 2 `3V3(OUT)` -> `VCC`; Pico `GND` -> `GND` | Planned. Confirm the actual CS1238 board is 3.3 V-safe and its bridge-reference configuration/excitation before power. |
| CS1238 digital | Pico `GP2` -> `SCK`; CS1238 `DT`/`DRDY-DOUT` -> Pico `GP3` | Planned. Both signals are 3.3 V logic. No level shifting is authorized until the received board is inspected. |
| Reference sensor | Instructor 5 N strain-gauge sensor, integrated on the INA101KU board assembly | Planned. The supplied PCB artwork shows an internal four-pad load-cell footprint. The green five-position rear terminal block is the only user wiring interface; do not add a separate sensor-input harness. |
| INA101 supply | Rear board terminals labelled `+V`, `-V`, `GND` -> verified dual bench supply | Required verification. `+V` and `-V` are the INA101KU bipolar amplifier rails (±5 V to ±20 V); do not power the amplifier from Pico 3.3 V. |
| Reference excitation | Rear board terminal labelled `5V` -> same dual-supply `+5 V` rail used for INA `+V` | Planned wiring; terminal purpose confirmed by the owner as the original Arduino 5 V input. It is bridge excitation, not an INA101 supply rail. This is a branch of the same physical dual-output bench supply, not a third supply. |
| INA101 output | Board-labelled `OUT` -> 1 kOhm series resistor -> Pico `GP26` / ADC0 | Required verification. Probe the output first. A negative or greater-than-3.3-V output must never reach Pico ADC0. |
| ADC reference | Board-labelled `GND` -> Pico `AGND` only after the supply/reference relationship is metered | Required verification. This is the analogue signal reference, not permission to tie unknown supply rails together. |
| DAQ ON/OFF switch | Pico `GP15` -> latching SPST switch -> Pico `GND` | Optional physical DAQ control. Firmware uses `INPUT_PULLUP`: switch ON closes to GND and reads LOW; switch OFF opens and reads HIGH. ON starts a run and OFF stops it; it does not control motor power or replace E-stop. |
| Motion marker | Pro Micro `GP1` -> Pico `GP14`; Pro Micro `TOOL_GND` -> Pico `GND` | Planned temporary test-only timing marker. Both are 3.3 V logic; never use `PC817C CTRL_GND`. Pico records the two marker edges on its own microsecond clock. |
| PC link | PC USB port -> Pico micro-USB | USB supplies Pico power and carries the CDC serial stream for the DAQ fixture. Pico `3V3(OUT)` then powers CS1238 #1 only. |

The production Pro Micro retains its existing GP0/GP1/3V3/GND CS1238 path when
the test fixture is removed. During the test GP1 is reassigned only as a
`MOTION_ACTIVE` output; it returns to CS1238 clock ownership when the fixture
is removed. The test harness temporarily gives CS1238 #1 its own Pico
connections; do not parallel either ADC's clock or data pins.

## Raw stream and PC storage

The Pico emits one record per CS1238 conversion at the measured delivered
rate, starting at the Pico `t = 0` event. It samples ADC0 immediately before
or after that conversion and preserves both acquisition timestamps:

```csv
toolhead_time_us,toolhead_cs1238_raw,reference_time_us,reference_adc_raw
0,5823412,8,1247
1563,5825518,1571,1251
```

The PC-side logger owns a dated run directory, `samples.csv`, `events.csv`, a
plain-text Pro Micro command/reply log, and `metadata.json`. Metadata includes
the PC wall-clock start, Pico firmware version, CS1238 configuration, INA101
supply/gain settings, sensor identities, and operator notes. No moving
average, tare subtraction, or force conversion is permitted in the acquisition
CSV.

The Pico also records `motion_start_us` and `motion_end_us` when its `GP14`
interrupt receives the Pro Micro's `MOTION_ACTIVE` rising and falling edges.
Those event times belong in a separate raw `events.csv` or clearly identified
event records, not inferred from PC command receipt time. The Pro Micro sets
the marker HIGH immediately before an actuator pulse and LOW immediately after
it ends; boot, stop, and fault leave it LOW.

Every completed run also requires the paper-ready figure package specified in
[`../report/FORCE_CALIBRATION_RESULTS.md`](../report/FORCE_CALIBRATION_RESULTS.md).
It overlays the two Pico channels with the Pico-timestamped Pro Micro marker,
while retaining the raw files and separately showing the force-transfer fit.

## Recommended minimum-change PC arrangement

Use two USB COM ports on the PC, with separate responsibilities:

1. **Pico 2 native USB:** the sole high-rate measurement stream. It emits the
   raw CS1238 and ADC0 values plus Pico microsecond timestamps.
2. **Existing USB-to-TTL adapter -> Pro Micro `Serial2`:** controlled `d`,
   `u`, `x`, and step-duration commands plus low-rate command/actuator status.
   It is already a USB connection at the PC but does not power the Pro Micro;
   adapter `VCC` stays disconnected.

This preserves the established 6 V -> S7V8F5 -> Pro Micro power path and
avoids changing the working toolhead controller for the calibration. The
currently staged E-07B actuator-step sketch already accepts short `d`/`u`
pulses and `x` stop through that service UART; its disconnected HX711 reports
are not calibration data and should be ignored. The integrated toolhead
firmware remains commissioning-locked and must not be used for force control.

The unavoidable new work is limited to Pico DAQ firmware and a PC logger. The
logger first starts Pico capture, then sends a low-rate Pro Micro pulse command
and records its text acknowledgement in a separate command log. Pico time,
not PC or Pro Micro receive time, remains the only time base used to compare
the two force sensors. Native Pro Micro USB CDC may be evaluated later after
the external-power/USB voltage check in
[`2026-09-16-promicro-external-power-usb-cdc-research.md`](../report/lab-notes/2026-09-16-promicro-external-power-usb-cdc-research.md)
passes.

## Required checks before live loading

1. With power removed, inspect and photograph both CS1238 boards and the
   reference-board rear terminal block. The INA101 board is visually identified
   as INA101KU with terminals `OUT`, `5V`, `+V`, `-V`, and `GND`, a 100 kOhm
   trim, a 4.3 kOhm fixed resistor, and an internal four-pad load-cell
   footprint. The rear terminal block is the only user wiring interface.
2. Complete E-07C bridge-resistance and `E+`--`E-` excitation checks for
   CS1238 #1 before accepting readings.
3. With power removed, continuity-map the rear terminals to the INA101KU
   SOL-16 pins: `OUT` to pin 1, `+V` to pin 2, `-V` to pin 10, and `GND` to
   pin 9 (`Common`). The 4.3 kOhm part is the likely gain resistor, giving
   approximately `G = 1 + 40 kOhm / 4.3 kOhm = 10.3 V/V`; the 100 kOhm pot is
   more likely the data-sheet-style offset trim. Confirm both conclusions by
   continuity before adjusting either control.
4. Power the INA101 only from its verified ± supply arrangement. Its labelled
   `5V` terminal is the original Arduino 5 V bridge-excitation input, not an
   INA101 amplifier rail; branch it from the same +5 V bench-supply rail used
   for `+V`. With the reference sensor unloaded and then gently loaded, meter
   `OUT` relative to board `GND` before connecting Pico ADC0. It must stay in
   the inclusive 0-3.3 V range with margin across the planned 5 N range.
5. Verify the Pico `AGND` signal-reference connection produces a stable ADC
   reading without creating an unexpected supply-to-supply current path.
6. Verify raw CS1238 and ADC records with no actuator power. Only then permit
   a guarded, operator-supervised loading test with the existing physical
   E-stop and main-power cutoff accessible.

The evidence and meter procedure behind this correction are recorded in
[`2026-09-18-ina101ku-instructor-pcb-datasheet-reconciliation.md`](../report/lab-notes/2026-09-18-ina101ku-instructor-pcb-datasheet-reconciliation.md).

## Setup checklist

This is a **bench-only, supervised** procedure. Stop at any unchecked
prerequisite; an unchecked item is not permission to improvise a connection.
The available repository firmware does not yet implement Pico dual-channel
DAQ or the PC logger, so this checklist ends at the hardware/readiness gate
until those programs are added and verified.

### 1. Make the bench safe

- [ ] Keep the 6 V toolhead actuator supply disconnected during all wiring and
  dry electrical checks. It is energized only after the dry-run gate passes.
- [ ] Keep the physical E-stop and the machine main-power cutoff reachable.
- [ ] Turn the bench supply outputs **off** and unplug the Pico USB cable.
- [ ] Disconnect the toolhead 300 g bridge completely from the Pro Micro and
  HX711 path. One bridge must have one ADC owner only.
- [ ] Place the Pico, CS1238, INA101 board, and reference sensor where no bare
  conductor can short to the plotter frame or another supply.
- [ ] Photograph the boards, cable colours, and terminal labels before making
  changes. Record board revision/markings in the future run metadata.

### 2. Power-off identification and meter checks

- [ ] On CS1238 #1, identify and label its actual `VCC`, `GND`, `SCK`,
  `DT`/`DRDY`, `E+`, `E-`, `A+`, and `A-` terminals. Do not rely on a generic
  HX711-form-factor pin order.
- [ ] Measure and record the toolhead bridge resistance and the isolated
  resistance between its signal/excitation conductors. Do not apply power if
  there is an unexpected short.
- [ ] Map the rear green-terminal pins labelled `OUT`, `5V`, `+V`, `-V`, and
  `GND` to the board traces. The owner has confirmed `5V` is the original
  Arduino 5 V bridge-excitation input; verify the other terminal-to-INA101
  mappings and absence of shorts before applying power.
- [ ] With power removed, measure the INA101 gain-network resistance at both
  trim extremes and record the results. Do not turn the trim during a loaded
  acquisition.
- [ ] Confirm the bench supply has two isolated, adjustable outputs suitable
  for the INA101 `+V` and `-V` rails. Do not substitute the Pico's 3.3 V rail
  or a single 5 V supply for these rails.

### 3. Wire the toolhead CS1238 channel

- [ ] Connect the 300 g toolhead bridge to **CS1238 #1 channel A**:
  `E+`, `E-`, `A+`, and `A-` by the inspected board labels.
- [ ] Connect Pico `3V3(OUT)` to CS1238 `VCC`.
- [ ] Connect Pico `GND` to CS1238 `GND`.
- [ ] Connect Pico `GP2` to CS1238 `SCK`.
- [ ] Connect CS1238 `DT`/`DRDY` to Pico `GP3`.
- [ ] Inspect every CS1238 connection against the wiring table and confirm no
  other MCU, HX711, or ADC remains connected to that bridge.
- [ ] Connect Pro Micro `GP1` to Pico `GP14` and Pro Micro `TOOL_GND` to Pico
  `GND` as a separate two-wire timing-marker pair. Confirm both boards are
  de-energized first and never use the isolated `PC817C CTRL_GND` node.

### 4. Wire and prove the reference path

- [ ] With bench outputs still off, series-link the two 5 V bench channels:
  channel 1 negative to channel 2 positive is the 0 V midpoint. Connect
  channel 1 positive to **both** INA `+V` and board `5V`, channel 2 negative
  to INA `-V`, and the midpoint to INA `GND`.
- [ ] Leave the INA101 `OUT` wire disconnected from Pico `GP26` initially.
- [ ] Power the INA101 from the verified dual supply and meter `OUT` relative
  to board `GND`, unloaded and under a gentle hand load. Confirm it stays
  inside **0–3.3 V with margin** and has the expected polarity throughout the
  intended 5 N range.
- [ ] Turn the bench output off before changing the signal wiring.
- [ ] Only after the output-span check passes, connect INA101 `OUT` through a
  1 kOhm series resistor to Pico `GP26`/ADC0 and connect INA101 `GND` to Pico
  `AGND`. Recheck that no negative or above-3.3 V voltage can reach ADC0.

### 5. Bring up the USB and acquisition chain

- [ ] Connect the Pico micro-USB cable directly to the PC. This powers the
  Pico and supplies CDC serial; it is not a power source for INA101 rails.
- [ ] Confirm the PC recognizes the Pico serial port and record its COM port.
- [ ] Flash the dedicated Pico DAQ firmware only after it exists, compiles, and
  has a documented version identifier. Do not use a Pro Micro trace as
  substitute data because it does not share the Pico timestamp base.
- [ ] Confirm the DAQ reports raw CS1238 values and raw ADC0 values with Pico
  microsecond timestamps, with no moving average, tare, or force conversion.
- [ ] Confirm the Pico reports and records a rising and falling `GP14` marker
  event while the Pro Micro is motor-unpowered. These Pico timestamps, rather
  than PC or USB receipt times, establish the command-to-force alignment.
- [ ] With the actuator supply still off, prove the latching GP15 DAQ switch:
  ON closes GP15 to Pico GND and starts a test; OFF opens it and stops the
  test. It must not change actuator power or substitute for the E-stop.
- [ ] Confirm the PC logger creates a new dated run directory containing the
  raw CSV, event CSV, Pro Micro command/reply log, and metadata before any
  loading test.
- [ ] Connect the existing 3.3 V USB-to-TTL service adapter to the Pro Micro
  command UART (`adapter RXD` <- `GP20`, `adapter TXD` -> `GP21`, and adapter
  ground -> `TOOL_GND`). Leave adapter VCC disconnected. This is the actuator
  command link; Pico USB remains the measurement-data link.

### 6. Dry-run acceptance gate

- [ ] With the toolhead actuator still unpowered, collect at least 30 seconds
  of unloaded raw data.
- [ ] Confirm timestamps are monotonic, neither data field is blank, and the
  CS1238 delivered sample rate is recorded rather than assumed.
- [ ] Confirm ADC0 remains within 0–3.3 V and does not show supply-related
  clipping or a large unexpected step when the reference sensor is touched.
- [ ] Stop the run. Preserve the raw CSV unchanged and add sensor identities,
  supply settings, gain-trim position, operator, and PC wall-clock time to
  metadata.

### 7. Supervised commanded-force calibration and shutdown

- [ ] Obtain operator approval before applying any load. Keep force below the
  known safe range of both sensors and the toolhead mechanics.
- [ ] Verify an accessible manual power-cutoff path for the toolhead 6 V rail.
  The documented machine E-stop does not by itself remove that rail.
- [ ] Energize the existing 6 V toolhead input only through its established
  path: DRV8833 motor rail plus S7V8F5 regulated 5 V supply to the Pro Micro.
  Do not apply 6 V directly to the Pro Micro or to Pico/INA101 wiring.
- [ ] Verify the Pro Micro boots safely and accepts its existing manual
  service-UART commands before placing the reference sensor in the force path.
- [ ] Start a new Pico raw-data run, then issue only small, controlled
  downward/upward commands to the Pro Micro. The Pico records the resulting
  CS1238 and reference-sensor data; it does not command the actuator.
- [ ] Stop immediately using the verified toolhead power cutoff if force,
  travel, output voltage, or communications are abnormal. Keep the E-stop
  accessible throughout.
- [ ] Stop the run before changing wiring, gain, supply settings, or mechanical
  alignment.
- [ ] Turn off the bench supply, unplug Pico USB, and only then rewire.
- [ ] Restore the toolhead bridge to its production controller path only after
  the calibration fixture is fully de-energized.

## Calibration interpretation

Calibrate the reference-sensor path independently into force first. Use its
timestamped force and the closest raw CS1238 sample to evaluate the toolhead
sensor's signed transfer, linearity, hysteresis, and residuals. Do not assume
the relationship is linear or copy resulting constants into the toolhead
controller until the force-path acceptance test is documented.
