---
id: RPSW-20261011-001
date: 2026-10-11
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
  - windows-software
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp
  - firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.h
  - firmware/pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino
  - tools/bed_mesh_probe.py
tags:
  - bed-mesh
  - probing
  - toolhead
  - telemetry
  - flatness
related:
  - HW-20261011-001
  - RPSW-20261001-001
  - ADR-007
---

# Bed mesh from the toolhead's M3 contact seek

## Summary

The machine can now probe its own bed with the hardware it already has: the
toolhead's M3 engage is a force-terminated contact seek, and its firmware now
exports the distance that seek travelled. A host tool drives the RP23NC and the
toolhead together, runs one M3 per map point, and writes a mesh CSV that the
existing `tools\bed_tilt_map.py` turns into a Klipper-style surface, screw
report, and residual map. No rewiring, no added sensor: the pencil body in the
pen mount is the probe tip.

## Reason

The operator asked for Klipper-style bed leveling with "M3 time and pen pressure
to dictate how the image of the round bed looks", and offered a service-UART
connection for any needed firmware change. The 2026-10-11 gap-map work
(`HW-20261011-001`) had left the measurement manual, one dial reading per point.
Reading the toolhead source showed the probe already exists: on every M3 the
controller homes toward the GP2 reference, drives bounded 10 ms/5 ms pulses,
stops when the CS1238 force crosses the contact threshold, and counts the
pulses. The only missing piece was a clean per-seek travel readout.

## Implementation

- `pressure_controller.{h,cpp}`: stores the per-seek travel
  (`last_seek_travel_fine_`) - the same coarse/fine weighted value the warm-seek
  EMA is built from - and exposes `lastSeekTravelFine()`. Cold seeks after the
  GP2 reference are fine-only, so their pulse count is already in the same
  units and is recorded too.
- `pro_micro_rp2350_toolhead.ino`: the snapshot/stream telemetry gains
  `last_seek_travel=%u`.
- `tools/bed_mesh_probe.py`: drives the RP23NC (telnet to the direct-link
  address, or USB serial) and the toolhead service serial. Per point: `M5`,
  move, `M3`, poll the `p` snapshot for `contact:1`, record
  `last_seek_travel`, `M5`. Supports polar meshes (carriage parked at a radius,
  bed indexed in 30 deg steps - the natural map for a round bed) and XY grids,
  repeats each point 2-3 times and reports the spread, converts travel to mm
  with a calibrated `--mm-per-pulse`, and writes the CSV that
  `tools\bed_tilt_map.py` reads. `--simulate` runs the whole pipeline against a
  synthetic bed for offline verification.
- Resolution: the actuator moves about 1.75 mm per 100 ms of full drive
  (E-09F), so a fine pulse is ~0.0875 mm; the map is good to roughly +/-0.05 mm
  per point after averaging and is calibrated directly by probing with and
  without a known shim under the pencil. The console prints the raw travel
  units next to the millimetres so the shim calibration uses the units directly
  (`mm_per_pulse = shim_mm / (units_before - units_after)`), independent of the
  default constant.

## Verification

- `tools\bed_mesh_probe.py --simulate` end-to-end: polar and grid runs, CSV
  written, `bed_tilt_map.py` recovered the synthetic tilt (0.277 mm/100 mm) and
  produced the mount report and PNG.
- The EMA-differencing fallback in the tool is retained for unflashed toolheads,
  but simulation showed the integer EMA quantizes the recovered travel
  (up to ~0.3 mm), which is why the firmware export is the primary path.
- Firmware **not compiled or flashed in this session** (no RP2350 toolchain
  here). The change is a member, an accessor, one telemetry field, and one
  assignment; it still needs a build, a flash, and a bench probe cycle.
- `python tools\docs_index.py --check` passes.

## Struggles and rejected approaches

- First design used the existing `warm_ema` stepping to recover per-seek
  travel; integer EMA arithmetic amplified quantization fourfold.
- The raw `home_seek_pulses` count was rejected as the primary metric because a
  10 ms coarse pulse counts once for twice the travel of a 5 ms fine pulse.
- Rejected: adding a new sensor or a dedicated probe input. The seek, force
  sensor, and service UART already carry the measurement; only the readout was
  missing.

## Follow-up 2026-10-11: the clearance is relative, so probing must retract

Reading the M5 path showed that the clearance is not an absolute height: normal
M5 proves the no-contact release band and then adds the `PEN_CLEAR_EXTRA_LIFT_MS`
air-gap pulse *from the last contact position*. A warm M3 therefore only
re-traverses the same ~1.2 mm gap, and its travel carries no bed-height
information. The absolute measurement is the cold seek that starts with GP2
asserted: each probe point now runs `M65 P0` (arm, toolhead retracts to the
lift-home switch), waits for `lift_home=1` in the snapshot, `M64 P0`, then `M3`.
`tools/bed_mesh_probe.py` does this by default (`--no-retract-each` restores the
warm-only cycle for non-probing experiments).

The first firmware export also turned out to be wrong for that path: cold seeks
mix 10 ms coarse and 5 ms fine pulses, so the raw pulse count is not linear in
millimetres. The controller now accumulates the travel of every seek pulse in
fine-pulse equivalents (coarse counts as two) for both warm and cold seeks, and
the warm-seek EMA is built from that same accumulator. This is a revision of
the same patch and needs one more flash of the same sketch; the host side is
unchanged apart from the retract cycle.

## Follow-up 2: the retract must not ride the magnetic arm line

The first bench probe attempt failed with "toolhead never reported the GP2 home
switch during retract", and the snapshot showed `mag=FAULT`. Root cause: the
GP28/Aux0 arm line is dual-purpose. On an arm edge during normal print the
toolhead decides between three outcomes: magnetic prerequisites ready -> start
the registration handshake; healthy but not ready -> request the end-of-print
full retract; already faulted -> enter another magnetic fault. A host retract
therefore silently does nothing whenever the magnetic subsystem is faulted, and
during production it can be captured by the registration handshake.

The integrated firmware now exposes a dedicated service command `h` ("full
retract to GP2") that sets the same `STATUS_FULL_RETRACT_REQUESTED` flag Core 0
consumes, bypassing the arm path entirely. `tools/bed_mesh_probe.py` uses `h`
by default; `--retract-via-arm` restores the M65 P0 behaviour for experiments.

## Follow-up 3: count the hold-correction travel after an early seek stop

The first five-probe calibration at bed centre returned 55, 61, 60, 37, 55
units: a tight cluster with one reading ~1.6 mm short. The short reading is a
seek that stopped on a force-noise spike at the threshold; the remaining
approach happened as downward hold-correction pulses, which the per-seek
export does not count. The controller now keeps `probe_travel_fine_`: the total
travel since the full-retract request, accumulating every seek pulse plus every
downward 5 ms hold correction, reset when the retract request is consumed.
Telemetry exports it as `probe_travel`, and the host tool prefers it over
`last_seek_travel`. The median across repeats remains the fallback for hosts
without the new field.

## Risks and follow-up

- Flash the patched toolhead firmware (USB or GP20/GP21 service UART), confirm
  `last_seek_travel` appears in `p`, then run the shim calibration for
  `--mm-per-pulse`.
- Probe contact is a ~40 g force event: keep the pencil tip's protrusion and the
  M5 clearance (1.2 mm) larger than the bed's height variation, or a point will
  fault during pen-up travel.
- The map repeats as long as the mechanical setup does; re-calibrate if the
  pencil is changed or the carriage is swapped.
- Open: whether to add a dedicated one-shot `PROBE` service command so the host
  does not need to interpret M3 handshaking.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.h`,
  `...cpp`, `...ino`: per-seek travel export and telemetry field.
- `tools/bed_mesh_probe.py`: host-side mesh probing and CSV output.
- `firmware/README.md`: toolhead section documents the new field.
- `docs/project/ENGINEERING_LOG.md`: session entry.
