# Lab Note: 2026-08-23 - Mains terminal and X sheath verification

## Objective

Verify the recorded AC terminal identities and the X motor-cable sheath landing
before any mains-power test.

## Result

The owner verified the following power-supply terminations:

- red conductor at the printed `L` terminal;
- blue conductor at the printed `N` terminal; and
- green wall-earth conductor plus green X motor-cable sheath/drain at the
  protective-earth symbol terminal.

## Evidence boundary

This verifies terminal identity and the reported landing only. It does not
verify PE-to-chassis resistance, the X shield's end-to-end continuity or its
isolation from DC `-V`, the enclosure, or powered mains behavior.

## Required next action

With all mains power removed, measure low-resistance continuity from the PE
terminal to the supply chassis and verify the X sheath has no continuity to DC
`-V` or motor-phase conductors. Complete the remaining E-11 power checks before
energizing a load.
