# RP23U5XBB Magnetic-Homing Candidate Build

This candidate configuration extends the verified 2026-08-14 baseline with:

- `PROBE_ENABLE=1` for the RP23CNC `PRB` input;
- `NGC_PARAMETERS_ENABLE=1` for probe coordinates and macro variables; and
- `NGC_EXPRESSIONS_ENABLE=1` for P100 calculations and flow control.

The source configuration is
[`../../../hardware/RP2040_RP23U5XBB_homing_candidate.json`](../../../hardware/RP2040_RP23U5XBB_homing_candidate.json).
It retains four axes, PWM spindle output, SD/YModem filesystem macros, W5500,
and the baseline control-input configuration.

## Gate Before Replacing the Baseline Artifact

1. Generate a candidate UF2 without overwriting `hardware/firmware.uf2`.
2. Record its build version, size, SHA-256, and complete `$I` report.
3. With TB6600 signal leads and motors disconnected, execute F-08 against a
   direct simulated `PRB` input.
4. Confirm `NEWOPT` reports expression support, `$pins` reports `PRB`, and
   `G65 P100 Q2`/flow-control parsing succeeds with the commissioning lock on.
5. The 2026-09-10 candidate passed direct and actual GP27/U3 PRB/G38 tests;
   the existing blue return is now at `PRB`. Next verify `G65 P100 Q1` with
   the installed active-low command order (`M65` -> `M64` -> `M65`).

This repository update does not generate, flash, or approve a replacement UF2.
