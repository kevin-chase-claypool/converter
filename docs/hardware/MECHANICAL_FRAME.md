# Mechanical frame and moving harness

This page records physical configuration that affects motion quality. It does
not replace measured drawings, photographs, or the wiring authority in
[`WIRING_TABLE.md`](WIRING_TABLE.md).

## Y drag-chain path

Current configuration, reported by the operator on 2026-10-25:

- The Y drag chain follows the 3030 extrusion for the full Y print travel.
- The former northeast rail pillar had a stairstep transition that forced the
  chain to climb as it approached the pillar.
- The installed replacement pillar has a straight face with no stairstep.

This change removed a recurring friction point that varied with Y position and
was consistent with feed-dependent striations. The operator reports that the
XY-only version of the affected print is now visually flawless. Rotating-bed
tracking remains a separate M-06 verification item.

The replacement part's dimensions, material, and model were not recorded. Do
not treat this note as a dimensional inspection. When servicing the frame,
preserve a straight, unobstructed chain path through the complete Y stroke and
check that the chain is not being lifted by a pillar edge, cable bundle, or
fastener.

Evidence:

- [`2026-10-25-m-13-drag-chain-pillar.md`](../report/lab-notes/2026-10-25-m-13-drag-chain-pillar.md)
- [`2026-10-25-bed-compensation-and-simultaneous-xy-a-motion.md`](../research/2026-10-25-bed-compensation-and-simultaneous-xy-a-motion.md)
