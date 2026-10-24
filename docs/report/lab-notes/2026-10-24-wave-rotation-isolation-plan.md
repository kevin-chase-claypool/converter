# Lab Note: 2026-10-24 - CMYK wave-rotation isolation test plan

## Objective

Determine whether the CMYK wave-screen spacing pattern is caused by bed motion
while the pen is down, and distinguish feed sensitivity from A-acceleration
sensitivity, using one mounted sheet.

## Configuration

- Hardware and firmware: current installed machine.
- Required starting settings: `$123=6000`, `$113=30000`.
- Pen: the same pen, pressure, and seating used for the failing 16:30 yellow
  print.
- Registration: one `G65 P113` before the base file only.
- Test files:
  - `samples/gcode/wave-rotation-isolation-base.gcode`
  - `samples/gcode/wave-rotation-isolation-low-a-accel.gcode`

## Procedure

1. Mount a fresh sheet and the test pen. Keep the sheet taped for both files.
2. Run `G65 P113` and record `$$`.
3. Run `wave-rotation-isolation-base.gcode` at 100 percent feed override.
   Do not change feed override during the run.
4. Photograph the completed six patches from above before changing settings.
5. Set `$123=3000`; confirm with `$$`.
6. Without moving or retaping the sheet, run
   `wave-rotation-isolation-low-a-accel.gcode`.
7. Photograph cases 7-8, then restore `$123=6000` and confirm with `$$`.

## Case map

| Case | Position | Motion |
|---|---|---|
| 1 | Top-left | A parked at 0, `F700` |
| 2 | Top-centre | `+5 deg` bed rotation during each row, `F700` |
| 3 | Top-right | `+10 deg` bed rotation during each row, `F700` |
| 4 | Middle-left | `+14.5 deg` bed rotation during each row, `F700` |
| 5 | Middle-centre | `+14.5 deg` bed rotation during each row, `F350` |
| 6 | Middle-right | `-14.5 deg` bed rotation during each row, `F700` |
| 7 | Bottom-left | Second-pass parked A0 control, `F700` |
| 8 | Bottom-centre | `+14.5 deg` bed rotation at `F700`, `$123=3000` |

## Acceptance and interpretation

- All eight patches should have four evenly separated parallel wave rows.
- If case 1 or 7 is clean and the rotating cases worsen, the A/rotation path is
  implicated.
- If case 5 is clean while case 4 is not, the remaining error is feed/rate
  sensitive.
- If case 8 is clean while case 4 is not, A acceleration/torque is implicated.
- If case 1 already shows the pattern, inspect pen contact, ink flow, X/Y
  carriage behavior, and paper mounting before changing A settings.

## Record

- Current status: ready to run; no result yet.
- Keep the `$$` captures and overhead photos with the measured case map.
