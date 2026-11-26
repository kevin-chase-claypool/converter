# Mechanical frame and moving harness

This page records physical configuration that affects motion quality. It does
not replace measured drawings, photographs, or the wiring authority in
[`WIRING_TABLE.md`](WIRING_TABLE.md).

## Rotating-bed print geometry

Current operator-reported and converter-configured geometry:

- Physical rotating-bed diameter: `18 in` (`457.2 mm`).
- Round paper-stock diameter: `15 in` (`381.0 mm`).
- Tape margin from every stock edge: `0.25 in` (`6.35 mm`).
- Intended drawing diameter: `14.5 in` (`368.3 mm`).
- Converter planning radius: `184.15 mm` (`7.25 in`).

The tape band between the 15-inch stock edge and 14.5-inch drawing circle is
`0.25 in` wide on every side. Preview draws the 18-inch bed, 15-inch stock, and
gantry reach circle separately.

The 14.5-inch drawn disc is an owner-specified geometry, not a completed
physical reach verification. Recheck the current HOME + REGISTER G54 envelope,
the tight +Y soft limit, and the actual taped-stock clearance before running a
full-disc production program. The active profile also reserves its `1.142 mm`
maximum correction inside the `184.15 mm` limit, producing a current nominal
planning radius of `183.008 mm` with a final corrected envelope no larger than
`184.15 mm`.

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
