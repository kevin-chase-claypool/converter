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
The PE terminal-to-supply-chassis path also passed. The powder-coated machine
structure is not used as the PE reference.

## Evidence boundary

This verifies terminal identity, the reported landing, and X-sheath isolation
from DC `-V`, and the PE terminal-to-supply-chassis path. It does not verify
the X shield's end-to-end continuity or isolation from motor phases, bonding of
the powder-coated machine structure, the enclosure, or powered mains behavior.

## Required next action

With all mains power removed, verify the X sheath has no continuity to
motor-phase conductors. Complete the remaining E-11 power checks before
energizing a load.
