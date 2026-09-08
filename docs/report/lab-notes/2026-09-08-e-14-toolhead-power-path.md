# Lab Note: 2026-09-08 - E-14 toolhead power-path verification

## Objective

Record the reported completion of the D36V50F6 6 V regulator, toolhead
perfboard, DRV8833, and S7V8F5 power-path gates.

## Reported results

- **E-14 passed:** the Pololu D36V50F6 output was a constant 6.05 V.
- **E-14B passed:** the completed toolhead perfboard and its intended power/
  logic wiring passed the owner’s inspection.
- **E-14C passed:** the ACEIRMC DRV8833 mapping and J2 inspection passed.
- **E-15A passed:** the owner confirmed the earlier TMAG test exercised the
  toolhead 5 V path successfully.

## Existing supporting evidence

The earlier E-14B record contains the prior continuity and local-power details;
the earlier E-14C record contains GP7 `ULT` near 3.3 V, GP6 `EEP` near 2.98 V,
and bidirectional N20 motion. This note records the owner’s final pass report
for their remaining inspection/configuration gates.

## Boundary and next action

E-15 remains open: characterize D36V50F6 voltage, ripple, current, and
temperature with the actuator under its intended loaded seek/hold/lift cases.
Do not treat the constant 6.05 V no-load result as that loaded qualification.
