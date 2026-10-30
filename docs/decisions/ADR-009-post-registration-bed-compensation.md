# ADR-009: Optional post-registration host bed compensation

- Status: accepted and implemented; base profile bench-verified, row-locked
  Wave physical verification pending
- Date: 2026-10-23
- Updated: 2026-10-30

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

The desktop converter selects the centered dense-v3 profile
`18bfb4ed1c33` by default. It covers the measured `165.100 mm` radius without
extrapolation, giving a 13.0-inch compensated diameter. The default 14-inch
stock diameter and 12.7 mm rim margin produce the same 165.1 mm drawable
radius. The existing Machine-tab path remains editable: **Browse...** selects a
replacement, **Default** restores this profile, and an empty path disables
compensation.

CMYK **Wave screen - equidistant rows** treats exact adjacent-row pitch as a
hard geometry constraint. Its default spacing guard keeps the selected profile
but applies a row-locked projection. The full measured field is evaluated in
the effective screen frame, then averaged across the perpendicular row
coordinate at each along-row position:

```text
C_row_locked(u) = average_v C_bed(u, v)
machine_xy = R(theta) * bed_xy + R(theta) * C_row_locked(u)
```

Every parallel row receives the same displacement at a given `u`, so their
relative spacing is unchanged. This retains the along-row and common part of
the measured correction; the row-dependent normal part is discarded because
it cannot coexist with an exact uniform lattice. Raw unconstrained
compensation remains an explicit operator opt-in.

Interactive preview defaults to fast nominal X/Y so dense artwork remains
responsive. Saved G-code applies the effective compensation path exactly.
The **Exact compensated preview (slow)** option makes the displayed moves use
the same correction path when coordinate parity matters for verification.

Measured paper errors are bed-frame displacements. Before storage, the
required correction is rotated into machine coordinates:

```text
C_machine(theta, p) = -R(theta) * e_bed(theta, p)
```

Adding the unrotated negated bed error directly to machine X/Y is invalid for
non-zero bed angles.

Angular interpolation also happens in the rotating bed frame. Stored corrections
are rotated back into bed coordinates at their measured angles, interpolated
there, and rotated into machine coordinates at the requested angle:

```text
e_0 = -R(-theta_0) * C_machine(theta_0, p)
e_1 = -R(-theta_1) * C_machine(theta_1, p)
C_machine(theta, p) = -R(theta) * lerp(e_0, e_1)
```

Directly interpolating the machine-frame correction vectors is invalid because
it shortens and misdirects the correction between angular samples.

P100 remains the only owner of magnetic registration and the physical rotation
centre. No grblHAL planner, macro, work-offset, or controller contract is
changed. Clearing or omitting the profile path leaves the uncompensated
program unchanged.

## Consequences

- Position- and angle-dependent residual error can be corrected without
  changing the artwork or choosing a different kinematics mode.
- New compensated G-code identifies bed-frame angular interpolation in its
  header. Files generated before that marker used machine-frame angular blending
  and must be regenerated before comparing compensated output.
- Saved G-code may use the profile, and exact preview mode must share its
  corrected endpoints and subdivision. Any coverage or correction-bound
  violation stops planning.
- Fast preview intentionally displays nominal machine X/Y and must identify
  itself as approximate. It is suitable for composition and motion review,
  not for measuring compensated placement on paper.
- Exact Wave row pitch and the raw non-uniform correction cannot both be
  guaranteed. The default Wave guard retains the maximal displacement that is
  common to all parallel rows and discards the incompatible normal variation.
  On profile `18bfb4ed1c33`, this retains `50.9-65.5 %` of raw correction
  energy before G-code quantization, depending on screen angle.
- Row-locked saved G-code identifies the source profile fingerprint,
  projection maximum, row angle, and `row_locked_projection` manifest mode.
  It must not be described as applying the raw two-dimensional field.
- The current default profile covers only the measured 165.100 mm field. Its
  measured coverage is valid only while bed, paper support,
  toolhead/carriage, pen clamp, and registration remain consistent.
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
- The post-repair profile `4bad792e35ad` supersedes `4c8270de8a74` after the
  NE drag-chain pillar repair. Its independent compensated verification
  reduced overall RMS from `1.744` to `0.218 mm`, maximum from `2.965` to
  `0.591 mm`, and improved every angle stage; all M-12 verification gates
  passed. The result verifies the measured `165.100 mm` field.
- The prior `4bad792e35ad` profile extended that field through the outer
  `6.350 mm` annulus to `171.450 mm`. Its maximum boundary correction is
  `2.783 mm`, below the 5 mm safety bound, but that annulus was not
  independently bench-verified.
- On 2026-10-29 the project owner explicitly promoted centered dense-v3
  `18bfb4ed1c33` despite independent verification missing the formal maximum
  and improvement gates. The verified field reduced every angle-stage RMS and
  aggregate RMS, but its maximum was `1.171 mm` and improvement was `11.6 %`.
  This is a documented owner override rather than a gate-qualified pass.
- A true X/Y scale or skew defect remains a controller/mechanical calibration
  issue rather than being folded into the fiducial-normalized residual map.
- The four-ink final-machine audit passes, but a physical comparison print is
  still required to establish whether the retained projected correction
  improves the printed residual without reintroducing visible row drift.
