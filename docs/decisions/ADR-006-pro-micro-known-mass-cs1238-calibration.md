# ADR-006: Use a Pro Micro-only known-mass method for CS1238 calibration

- Status: accepted; bench evidence pending
- Date: 2026-09-21

## Context

The proposed temporary calibration fixture used a Pico 2, a second ADC, and an
instructor-supplied 5 N reference sensor/INA101KU board to compare applied pen
force with the installed 300 g load cell. The temporary fixture was not wired
or hardware-qualified. It added two USB data paths, a dual-supply reference
sensor, synchronization concerns, and an experiment-only load path.

The installed CS1238 and 300 g load cell can instead be characterized directly
with the available precision weights: 4 × 5 g, 3 × 10 g, and 2 × 20 g. Those
weights cover total static loads from 0 through 70 g in 5 g increments, which
includes the intended initial 40–60 g pen-pressure range.

## Decision

- Use only the installed Pro Micro RP2350, CS1238, and 300 g load cell for
  E-09C calibration.
- Feed the Windows capture/fit application through the Pro Micro's native USB
  port. The app is an operator/data-recording tool, not a second controller.
- Keep the actuator 6 V rail disconnected during this calibration. No motor
  command, M3/M5 input, DRV8833, or Pico pin participates.
- Retain every timestamped raw CS1238 sample. Use a repeatable final-half
  capture mean only for the proposed raw-to-grams fit.
- Measure at least three loading and three unloading 0–70 g passes, and review
  residuals/hysteresis before using the result in any later controller work.

## Consequences

- The temporary Pico 2, INA101KU, second-ADC, and reference-sensor fixture is
  removed from the active calibration workflow.
- The resulting equation calibrates the CS1238/load-cell reading to applied
  static precision mass in the installed vertical force path. It does not by
  itself prove actuator dynamics, contact behavior, or a safe moving-average
  control gain.
- Later actuator-response and force-control work must be a separate bench
  phase with its own safety envelope and evidence.
