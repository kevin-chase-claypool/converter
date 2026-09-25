---
id: RPSW-20260925-001
date: 2026-09-25
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
status: verified
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - toolhead
  - pen-clear
  - t-01h
---

# Accept T-01H and enable the pen-clear status

## Summary

Flipped `PEN_CLEAR_VALID` to `true` after T-01H was accepted, enabling the
`STATUS_CLEAR_READY` status that the GP27 normal-print handshake will consume.

## Reason

T-01H required the measured pen-tip gap and a release force trace. The gap was
measured at about 1.75 mm, and a four-cycle warm capture recorded contact at
~40-47 g and release clearing to ~0 g, with no drag across production prints
that each exercise hundreds of M3/M5 cycles.

## Implementation

- `toolhead_config.h`: `PEN_CLEAR_VALID` `false -> true` with a dated comment.
  `GP27_NORMAL_STATUS_ENABLED` remains false, so this only enables the
  clear-ready status flag (reported in telemetry and available to the handshake
  path); it does not itself start any controller wait.

## Verification

- `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350` builds
  cleanly.
- Bench evidence: `docs/report/lab-notes/2026-09-25-t-01h-clearance-confirmed-across-print-runs.md`.

## Struggles and rejected approaches

The pen was initially clamped too high, so the cold seek exhausted its 100-pulse
budget without reaching the paper and also produced a `CS1238 reading
implausible` fault. Dropping the pen within the carriage fixed both. The warm
seek overshoots contact to ~40-47 g; this is within the 30-50 g band and is
accepted for this non-precision machine, tracked separately from T-01H.

## Risks and follow-up

- The warm-seek contact overshoot climbs slightly across cycles and is tracked
  as a separate force-control item, not a clearance item.
- `cs1238_rejects` remains intermittent; the header may need a more permanent
  fix than reseating if the burst rate rises again.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`
- `docs/report/lab-notes/2026-09-25-t-01h-clearance-confirmed-across-print-runs.md`
