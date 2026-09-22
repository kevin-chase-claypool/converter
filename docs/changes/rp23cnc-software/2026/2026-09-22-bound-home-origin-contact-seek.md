---
id: RPSW-20260922-020
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - contact-seek
  - cs1238
  - pen-pressure
related:
  - T-02
  - T-01J
---

# Bound Home-Origin Contact Seek

## Summary

The supervised Pro Micro build now distinguishes an M3 command issued at GP2
full retract from routine M3 after the normal M5 clearance gap. The home-origin
case uses force-checked short DOWN pulses and faults safely if it cannot find
paper within configured bounds. A one-shot status includes the number of
completed seek pulses.

## Reason

The user reported the installed pen approximately 12 mm above paper while the
integrated status showed `pressure=LIFTED` and `lift_home=1`. The existing
100 ms M3 path was intended to restore about a 1.75 mm ordinary clearance gap,
not to span the full-retract-to-paper distance; force correction had no
initial-contact bound.

## Implementation

- From GP2 pressed, M3 enters `HOME_SEEK_CONTACT`: 5 ms full-drive DOWN pulse,
  driver sleep, then a 250 ms CS1238 settling interval before the next
  decision.
- Stop and transition to force hold at the configured 35 g raw contact
  threshold. The independent 60 g hard-force guard remains active.
- Stop/fault on 160 pulses, 45 seconds, 30 pulses without the lift-home switch
  releasing, sensor loss, cancellation, or the hard-force limit.
- After the operator inspects a fault, `c` may run the bounded UP-only recovery
  to GP2 even while the force remains above the hard threshold; it cannot
  restart downward seeking. It latches manual M5 so a held GP29 M3 cannot
  automatically restart the seek after recovery.
- From GP2 released, retain the short 100 ms normal engage move. Both paths
  retain the existing force acquisition timeout and moving-average corrections.
- Add `home_seek_pulses=<completed>/<limit>` to status snapshots for quiet
  progress checks.

The pulse count and 45-second ceiling are bench candidates based on the
reported approximate 12 mm gap and earlier E-09F travel observation; they are
not per-tool validated travel constants.

## Verification

- Added compile-time decision tests covering pulse start/stop timing, settling,
  force threshold, cancellation, budget, and timeout.
- Arduino RP2350 compile passed with
  `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350`.
- `python tools/docs_index.py --write` and `--check` passed.
- Hardware T-02/T-01J seek, force, switch-release, and per-tool clearance
  checks: pending. The source has not been flashed as part of this change.

## Struggles and rejected approaches

The first design would have reused the 100 ms normal M3 move and let the force
loop continue trying to acquire contact. That conflated two very different
starting positions and had no bounded initial-contact path. Extending the
single open-loop drive was rejected because it could push the pen into paper
without an intervening force reading.

## Risks and follow-up

Actual travel per 5 ms pulse, settling behavior, and the press-to-release
distance at GP2 remain toolhead/mechanism dependent. Before any plot, run the
supervised home-origin T-02 procedure with the cutoff reachable; inspect
`FAULT` before clearing it. T-01J must validate each pen and clamp-height
combination. Existing force-hold pulse response is not proven by this test.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`:
  home-origin state machine and bounded contact acquisition.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/contact_seek_policy.h`:
  deterministic seek decision policy and compile-time cases.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`:
  pulse-count status field.
- `firmware/pen_pressure/README.md`, `firmware/pen_pressure/CONTROL_STRATEGY.md`,
  `firmware/README.md`, `docs/integration/INTERFACES.md`,
  `docs/testing/TEST_PLAN.md`:
  updated current behavior and validation path.
- `docs/report/lab-notes/2026-09-22-t-02-home-contact-seek-setup.md`:
  records the observed starting state and pending physical test.
- `docs/project/ROADMAP.md`, `docs/project/ENGINEERING_LOG.md`:
  status and engineering decision.
