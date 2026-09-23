# Lab Note: 2026-09-23 - F-05 spindle-enable polarity

## Objective

Determine the RP23CNC spindle-enable (`ENA`) output polarity as it drives the
toolhead M3/M5 input, and confirm that `M3` engages and `M5` lifts through the
real controller-to-toolhead path.

## Configuration

- Hardware revisions: RP23CNC / `RP23U5XBB` V1.01; SparkFun Pro Micro RP2350
  toolhead with the PC817C interface board (U1 = M3/M5 command channel).
- Wiring/pin map: RP23CNC spindle group `ENA` to PC817C `J1.2` (U1 LED
  cathode); RP23CNC `5V` to `J1.1` `CTRL_5V`; RP23CNC control `GND` to `J1.5`
  `CTRL_GND`; U1 collector to Pro Micro `GP29`. See `WIRING_TABLE.md` rows
  `TH-001A`, `TH-001A-RT`, `TH-001B`.
- Firmware commit/build: toolhead `f03a74a`
  (`firmware/pen_pressure/pro_micro_rp2350_toolhead`); RP23CNC installed grblHAL
  homing-candidate build (see `firmware/grblhal/config/build-record.md`).
- grblHAL settings: `$16=1` (Invert spindle signals — bit 0, spindle enable).
  `$14=6` (invert control inputs) unchanged.
- Converter settings/sample: none; this is a controller/toolhead test.
- Instruments: no meter reading was captured. The result is functional
  (observed motion) plus the toolhead telemetry `cmd=` field.

## Code, commands, and configuration used

```text
ioSender console (RP23CNC):
  $16              query  -> $16=1
  $16=1            write  -> ok
  <reset>          Ctrl-X or power cycle; $16 is reboot-required
  M3
  M5

Arduino IDE Serial Monitor (toolhead, 115200):
  a                return to GP29 / M3-M5 control
  p                one-shot telemetry snapshot
  c                clear a latched fault
```

## Procedure

1. Powered the RP23CNC and the toolhead; pen installed with paper under the tip.
2. Sent `$16=1` in ioSender, then reset the controller.
3. Sent `a` in the toolhead console to return to GP29 control, then `p` to read
   the rest state.
4. Sent `M3` in ioSender and observed the toolhead state and motion.
5. Sent `M5` in ioSender and observed the toolhead state and motion.

## Results

- At rest with `$16=1`: toolhead reports `pressure=LIFTED`, `cmd=M5`. It no
  longer engages when the controller powers up.
- `M3`: the toolhead descends (pen down).
- `M5`: the toolhead lifts (pen up).
- Fail-safe direction: the toolhead input uses a 3.3 V pull-up (`R3`); with the
  optocoupler off (controller idle or unpowered) `GP29` reads high and the
  toolhead holds `LIFTED`. Disconnecting the `ENA` wire also left the toolhead
  lifted, confirming the input is the only engage path.
- Before the fix (`$16=0`), the toolhead saw a permanent M3 at controller
  power-up, ran the home contact seek, and latched
  `M3 home contact seek pulse budget exhausted` at 100/100 pulses.
- One CS1238 conversion (`-6,679,681` raw) was rejected and absorbed with no
  fault; `$16` also cleared a transient magnetic-reader `FAULT` state after
  reset.

## Difficulties and corrective actions

- Incorrect polarity assumption: the interface was designed assuming the
  RP23CNC spindle `ENA` sinks on M3 (active-low). It does not — at idle it held
  the optocoupler LED on, so the toolhead read a permanent M3 and drove the pen
  down at controller power-up. Diagnosed by disconnecting the `ENA` wire (no
  engagement) and by reading the toolhead `cmd=` field. Corrected with the
  controller setting `$16=1`; no optocoupler change was required. Repeat result:
  `M3` down, `M5` up, idle `LIFTED`/`cmd=M5`.
- Unexplained power event: mid-session the RP23CNC stopped powering up on 12 V
  with the `SWC USB` selector already on `SWC`. It returned to normal without a
  documented root cause. The cause and any corrective action remain unrecorded;
  treat it as an open risk until explained.

## Interpretation

The RP23CNC spindle-enable output is active-high by default, which is inverted
from this interface's active-low optocoupler input. grblHAL exposes a runtime
invert (`$16` bit 0), so the polarity is corrected in controller configuration
rather than hardware. The fail-safe is preserved: any loss of controller power
or the optocoupler leaves `GP29` high, which is pen-up.

## Decisions and next action

- Recorded `$16=1` as part of the controller configuration
  (`firmware/grblhal/config/machine-settings.md`).
- `F-05` direction and fail-safe are now demonstrated. `F-05A` (the `P115`/`PRB`
  pen-transition handshake) remains open and gated.
- Next: re-confirm the `M3`/`M5` behavior over a few repeated cycles and capture
  the `ENA` meter levels (idle/M3/M5) to complete the electrical record, then
  proceed to the `T-01H` normal-clearance run.
