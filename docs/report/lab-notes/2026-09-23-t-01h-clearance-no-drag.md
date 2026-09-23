# Lab Note: 2026-09-23 - T-01H clearance: no drag over repeated M3/M5

## Objective

Check whether the staged 57 ms M5 clearance actually lifts the pen enough that a
normal pen-up travel move leaves no mark — the last toolhead gate before
drawing.

## Configuration

- Hardware revisions: SparkFun Pro Micro RP2350 toolhead with the PC817C
  interface board; RP23CNC / `RP23U5XBB` V1.01.
- Wiring/pin map: RP23CNC spindle `ENA` to PC817C `J1.2` (U1); U1 collector to
  GP29. See `WIRING_TABLE.md` rows `TH-001A` and `TH-001B`.
- Firmware commit/build: toolhead `f03a74a`
  (`firmware/pen_pressure/pro_micro_rp2350_toolhead`, supervised
  `MECHANICAL_PRELOAD_MODE`).
- grblHAL settings: `$16=1` (invert spindle enable).
- Converter settings/sample: none; command-driven test.
- Instruments: none. Clearance was judged by the absence of a mark during the
  inter-stroke jog.

## Code, commands, and configuration used

```text
ioSender console (RP23CNC):
  M3    engage / pen down
  M5    lift / pen up
  <jog X or Y a few mm between M5 and the next M3>

Arduino IDE Serial Monitor (toolhead, 115200):
  a     return to GP29 control
  p     snapshot
  c     clear a latched fault
```

## Procedure

1. Pen installed, paper under the tip, toolhead parked.
2. Alternated `M3` and `M5` from ioSender for roughly 10-20 cycles.
3. Between each `M5` and the next `M3`, jogged X/Y a few mm.
4. Watched for any mark from the jog and for any fault.

## Results

- Every `M5` left the pen clear enough that the inter-stroke jog produced no
  mark.
- Every `M3` returned to contact.
- No cycle faulted.

## Difficulties and corrective actions

None encountered. The pen-up path had earlier been the symptom of the
spindle-enable polarity problem, but that was fixed separately
(`$16=1`; see the same-date F-05 lab note); this run used that corrected build.

## Interpretation

The staged 57 ms clearance behaves correctly for the supervised bench build:
the pen clears on `M5` and re-contacts on `M3` without drag across repeated
cycles. This is behavioral evidence, not a measurement.

## Decisions and next action

- Recorded as a T-01H partial result; `PEN_CLEAR_VALID` stays `false` until the
  measured record exists.
- To close T-01H fully, capture the pen-tip gap, the force trace with
  `F_contact_on` / `F_release_off`, the exact cycle count, and a 30-cycle run
  during a representative pen-up travel move.
- Next: generate a small converter drawing and run it through ioSender as the
  first end-to-end plot.
