# ADR-009: Optional post-registration host bed compensation

- Status: accepted for implementation; bench profile pending
- Date: 2026-10-23

## Context

P100 owns physical bed-centre and angular-index registration. Repeated
calibration photographs show that a single centre vector leaves a substantial
position-dependent residual, so changing P100 again cannot remove the observed
striations. The residual can vary with both bed XY and bed angle, and some
future jobs need the correct behaviour even before the mechanical bed plane or
carriage coupling is eliminated.

## Decision

Add an optional host-side residual map with this transform:

```text
machine_xy = R(theta) * bed_xy + correction(theta, bed_xy)
```

The existing planner still chooses `theta` from nominal bed geometry.
Compensation is applied afterward to the selected machine X/Y points in both
preview and G-code. The map is periodic in theta, uses measured bed-frame XY
samples, has explicit radial coverage, and rejects individual corrections
above 5 mm. Its fiducial fit removes common sheet translation, rotation, and
scale so P100 registration is not double-compensated.

P100 remains the only owner of magnetic registration and the physical rotation
centre. No grblHAL planner, macro, work-offset, or controller contract is
changed. A missing profile leaves the uncompensated program unchanged.

## Consequences

- Position- and angle-dependent residual error can be corrected without
  changing the artwork or choosing a different kinematics mode.
- Preview and saved G-code must share the profile, corrected endpoints, and
  subdivision. Any coverage or correction-bound violation stops planning.
- The map is only valid inside its measured field and only while bed, paper
  support, toolhead/carriage, pen clamp, and registration remain consistent.
- This software correction is not evidence that the bed is flat. A profile
  should be accepted only after the measurement analyzer's complete-data and
  leave-one-station-out gates pass, and a compensated verification sheet must
  confirm that the residual shrinks.
- A true X/Y scale or skew defect remains a controller/mechanical calibration
  issue rather than being folded into the fiducial-normalized residual map.
