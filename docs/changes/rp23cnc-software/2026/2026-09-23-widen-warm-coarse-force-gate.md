---
id: RPSW-20260923-010
date: 2026-09-23
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - t02
  - contact-seek
  - learning
related:
  - RPSW-20260923-009
---

# Widen the warm coarse-phase force gate

## Summary

The warm coarse phase now stops at about 3 g of force instead of sharing the 1 g
coarse/fine threshold, so an M5 cycle whose clear residual reads high no longer
skips the coarse travel entirely.

## Reason

The first bench run of the travel learning showed the coarse phase enabling or
skipping at random. The M5 clear residual varied 4,340-6,516 raw across six
cycles, and the coarse phase was gated on the shared 1 g threshold of 5,039
raw. Cycles entering below the gate used coarse travel and finished in 13-14
pulses; the one cycle entering at 6,516 raw skipped coarse entirely and took 27
pulses. See
[`2026-09-23-t-02-learned-travel-first-run`](../../../report/lab-notes/2026-09-23-t-02-learned-travel-first-run.md).

## Implementation

- `toolhead_config.h`: added `SEEK_WARM_COARSE_FORCE_GATE_RAW` (15,116 raw,
  about 3 g).
- `pressure_controller.cpp`: the coarse-phase force gate is now that value on a
  warm seek and the unchanged 1 g coarse/fine threshold on a cold start.

The cold-start gate is deliberately left at 1 g: its 12 mm gap gives ample
margin, and the wider gate is only needed where a clear-state residual can sit
near the threshold.

## Verification

- Compiled for `rp2040:rp2040:sparkfun_promicrorp2350` with `arduino-cli`
  1.5.1: passed, 81784 bytes program storage and 16220 bytes dynamic memory.
- `python tools\docs_index.py --write` and `--check` pass.
- Bench confirmation is required. Every warm cycle should now use the coarse
  phase, so the pulse count should stay near 13-14 regardless of the residual.

## Struggles and rejected approaches

Gating on the rise above the M3 entry force was considered, since that is the
physically meaningful signal, but it needs the entry force stored per seek and
the fixed 3 g gate already clears the observed residual band with margin.
Raising the shared coarse/fine threshold instead was rejected because it would
also loosen the cold-start switch, which does not need it.

## Risks and follow-up

Three grams is a supervised candidate derived from one six-cycle run. If a
coarse pulse ever lands on paper, the reserve, the budget cap, and the 60 g
guard remain the protection, and the gate should come back down. The wider gate
also means the coarse phase can run slightly closer to contact than before,
which the repeat run should confirm.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: warm coarse force gate.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`: apply the gate only to the warm seek.
- `firmware/pen_pressure/README.md`, `firmware/pen_pressure/CONTROL_STRATEGY.md`, `docs/integration/INTERFACES.md`: document the gate.
