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

The owner also meter-verified that the X sheath has no continuity to DC `-V`.

## Evidence boundary

This verifies terminal identity, the reported landing, and X-sheath isolation
from DC `-V`. It does not verify PE-to-chassis resistance, the X shield's
end-to-end continuity or isolation from motor phases, the enclosure, or powered
mains behavior.

## Required next action

With all mains power removed, measure low-resistance continuity from the PE
terminal to the supply chassis and verify the X sheath has no continuity to
motor-phase conductors. Complete the remaining E-11 power checks before
energizing a load.
