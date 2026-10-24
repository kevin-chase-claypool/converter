# ADR-009: Optional post-registration host bed compensation

- Status: accepted, implemented, and bench-verified
- Date: 2026-10-23

## Context

P100 owns physical bed-centre and angular-index registration. Repeated
calibration photographs show that a single centre vector leaves a substantial
position-dependent residual, so changing P100 again cannot remove the observed
striations. The residual can vary with both bed XY and bed angle, and some
future jobs need the correct behaviour even before the mechanical bed plane or
carriage coupling is eliminated.

## Decision

Add a host-side residual map with this transform:

```text
machine_xy = R(theta) * bed_xy + correction(theta, bed_xy)
```

The existing planner still chooses `theta` from nominal bed geometry.
Compensation is applied afterward to the selected machine X/Y points in both
preview and G-code. The map is periodic in theta, uses measured bed-frame XY
samples, has explicit radial coverage, and rejects individual corrections
above 5 mm. Its fiducial fit removes common sheet translation, rotation, and
scale so P100 registration is not double-compensated.

The desktop converter selects the current verified profile by default. The
existing Machine-tab path remains editable: **Browse...** selects a measured
replacement, **Default** restores the verified profile, and an empty path
disables compensation.

Measured paper errors are bed-frame displacements. Before storage, the
required correction is rotated into machine coordinates:

```text
C_machine(theta, p) = -R(theta) * e_bed(theta, p)
```

Adding the unrotated negated bed error directly to machine X/Y is invalid for
non-zero bed angles.

P100 remains the only owner of magnetic registration and the physical rotation
centre. No grblHAL planner, macro, work-offset, or controller contract is
changed. Clearing or omitting the profile path leaves the uncompensated
program unchanged.

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
- The first 2026-10-23 profile (`911d2694c8c9`) passed its internal fit but
  failed the compensated print because of the missing frame rotation. The
  corrected profile `2cdf3731de4a` passed the independent before/after
  verification: overall RMS fell from `0.581` to `0.338 mm`, maximum from
  `1.309` to `0.752 mm`, and error by `41.9 %`. A localized residual remains
  at station 09/14 near A=270; further accuracy requires mechanical
  plane/runout and carriage diagnosis rather than refitting the verification
  sheet into the profile.
- A true X/Y scale or skew defect remains a controller/mechanical calibration
  issue rather than being folded into the fiducial-normalized residual map.
