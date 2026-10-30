# Row-locked bed compensation for equidistant Wave screens

**Date:** 2026-10-30

## Question

Can the converter apply the complete measured bed-compensation field as the
last process while keeping every CMYK Wave row on one uniform machine-space
lattice?

## Conclusion

Not as an arbitrary two-dimensional displacement. The final transform must
trade part of the measured field for the hard row-spacing invariant.

The selected implementation is a **row-locked projection**:

1. Generate and prove the complete equidistant Wave image in paper space.
2. Evaluate the full measured profile at every point.
3. Resolve it into the measured profile's screen-frame axes.
4. For each along-row coordinate `u`, average the complete field across the
   perpendicular coordinate `v`.
5. Apply that one common displacement to every row at `u` as the final
   machine-XY transform.

This retains the mesh's along-row positional correction and common translation.
It discards only the component that varies between rows and changes pitch.
Every row receives the same displacement at a given `u`, so row-to-row spacing
is unchanged by construction.

## Why the full field cannot do both

Let adjacent source rows be:

```text
p0 = (u, v)
p1 = (u, v + h)
```

After an additive displacement field `D(u, v)`, their separation is:

```text
p1' - p0' = (0, h) + D(u, v + h) - D(u, v)
```

The norm of that vector is generally not `h`. It equals `h` for all points and
all row pairs only when `D` is an isometry, such as a translation or rotation.
A nonuniform measured correction cannot be an isometry unless its differential
is orthonormal everywhere.

That proof is local and does not require an external fitting model. The current
profile is also demonstrably nonuniform: it spans eight measured angles and has
a `1.141625 mm` maximum correction
([profile](../../samples/gcode/bed-error-compensation-2026-10-29-dense-v3-centered.json)).

## Approaches evaluated

| Approach | Result |
|---|---|
| Apply the raw profile after a uniform Wave screen | Fails the hard invariant. The preserved Ben2 set measures `0.224830-0.323477 mm` final-machine gap spread. |
| Disable compensation | Preserves spacing but violates the requested final mapping and discards all correction. Rejected as the endpoint. |
| As-rigid-as-possible deformation | Reduces local distortion, but it is an energy objective rather than a hard per-row distance constraint ([Igarashi et al., 2005](https://doi.org/10.1145/1186822.1073323)). It cannot certify the existing `0.005 mm` acceptance bound. |
| Nonlinear constrained minimisation | Can encode hard row constraints, but solving and proving a dense profile for every CMYK angle is much larger than the required transform. The row-common projection is the closed-form constrained solution. |
| Inverse-warp every source point so the raw profile lands on a machine lattice | Uses all displacement numerically, but cancels the intended positional correction physically. It would make the mesh appear active only in the command text, so it is not a valid bed correction. |
| Row-locked projection | Uses the complete profile to calculate the admissible field, preserves exact row spacing, and leaves a measurable positional correction. Selected. |

## Measured survival

The proposed production sampling grid has 129 along-row columns and 33
perpendicular samples per column. For profile `18bfb4ed1c33` at a parked bed,
the projected correction preserves this share of the raw displacement energy:

| Ink | Screen angle | Raw RMS | Projected RMS | Retained energy |
|---|---:|---:|---:|---:|
| Cyan | `15 deg` | `0.469636 mm` | `0.348369 mm` | `55.0 %` |
| Magenta | `75 deg` | `0.475221 mm` | `0.384489 mm` | `65.5 %` |
| Yellow | `0 deg` | `0.464636 mm` | `0.331569 mm` | `50.9 %` |
| Black | `45 deg` | `0.474751 mm` | `0.370416 mm` | `60.9 %` |

The discarded part is the row-dependent normal field that the uniform-lattice
requirement makes physically incompatible. The output must name this mode in
the set manifest and G-code header; it must not claim that the raw correction
was applied unchanged.

## Validation result

Applying the row-locked field to the four preserved Ben2 drawing geometries
reduced final-machine adjacent-gap spreads to:

| Ink | Raw compensated spread | Row-locked spread |
|---|---:|---:|
| Cyan | `0.240553 mm` | `0.002432 mm` |
| Magenta | `0.231895 mm` | `0.002255 mm` |
| Yellow | `0.323477 mm` | `0.000115 mm` |
| Black | `0.224830 mm` | `0.001541 mm` |

All four are below the existing `0.005 mm` bound. The result is a 199-column
machine-space audit of emitted `X/Y`, not an inverse-decoded paper-space
measurement.

## Constraints and follow-up

- The present audit contract is XY-only because a changing bed angle adds a
  separate rotation-dependent row geometry.
- The projected field is intentionally not equal to the raw two-dimensional
  displacement. Documentation and saved metadata must distinguish
  `row_locked_projection` from `full_unconstrained`.
- A physical comparison print remains mandatory. Software geometry does not
  prove that the compensated pen position improves on the machine.
- `docs/report/lab-notes/2026-10-30-ben2-yellow-row-end-boundary.md` contains
  the prior raw-compensation evidence; this note supersedes its recommendation
  to omit the profile from Wave jobs.
