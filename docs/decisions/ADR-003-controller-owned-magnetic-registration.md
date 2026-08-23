# ADR-003: Controller-owned magnetic registration over the existing interface

- Status: accepted for implementation; commissioning gated
- Date: 2026-08-22

## Context

Physical X/Y limit switches establish travel boundaries but do not locate the
rotating bed's true center. The fixed-height TMAG5273 can observe center and
outer index magnets, but the existing isolated interface carries only three
signals and no numeric data channel. One threshold crossing is an edge, not a
center. Adding moving-harness conductors is undesirable.

## Decision

Use a controller-resident grblHAL filesystem macro to perform every startup
home and registration sequence. It physically homes X/Y, captures multiple
TMAG entry/exit chords in a serpentine raster, computes their area centroid,
and registers G54 X0/Y0. It then captures the outer magnet on two consecutive
bed revolutions and registers G54 A0.

The Pro Micro RP2350 remains a one-bit magnetic front end. Core 0 owns pressure,
lift, HX711, actuator, and safety. Core 1 owns TMAG sampling and the GP28/GP27
protocol. The existing Aux0/GP28 and GP27/U3 pair uses a two-phase handshake:
readiness acknowledgement, release, then threshold-state arm. ENA/GP29 remains
the M3/M5 pressure command. No new toolhead-to-controller wire is added.

The candidate uses RP23CNC `PRB` and G38 entry/release capture. The installed
GP27/U3 endpoint remains `LIMA` until F-08 proves the exact build and isolated
path. Production motion is locked until measured constants and the named
commissioning tests are complete.

## Consequences

- The Windows converter and service USB are not in the real-time homing loop.
- A threshold edge can never be confused with the computed center.
- G54 carries bed center and angular registration; machine coordinates remain
  tied to physical X/Y switches.
- Every startup performs the full raster before A registration.
- The known-good baseline UF2 remains recoverable while the probe-enabled
  candidate is evaluated.
- F-08, E-18, M-08, M-09, M-10, and fault-path testing are acceptance gates.
