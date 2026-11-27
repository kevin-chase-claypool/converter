# ADR-013: Gate CMYK release on pointwise G-code registration

- Status: accepted and implemented; software registration verified, physical
  four-pen registration pending
- Date: 2026-11-27

## Context

A printed CMYK set showed yellow and magenta visibly shifted and cyan roughly
`10 mm` off when its program began. The saved test set was generated before the
shared page-frame fix and had registration crosses disabled.

The existing post-save audit read all four programs, but it compared only
program identity, G54 frame, reach, hashes, gross bounds, and centres. A whole
program could be translated by `10 mm` and still pass that audit. Those checks
are necessary release guards, but they are not pointwise registration evidence.

CMYK layers cannot be compared path-for-path because each ink contains a
different screened image. The set needs common geometry whose final emitted
machine coordinates can be recovered and compared.

## Decision

CMYK artwork sets use four named corner registration crosses. Each cross has
two short arms, a stable ID such as `CORNER-NW`, and explicit metadata that
preserves its pre-offset centre and the intended pen offset through the SVG,
planning, compensation, and G-code stages.

The final G-code carries one comment per arm:

```text
(registration mark id=CORNER-NW arm=horizontal
 center=x,y offset=dx,dy mm)
```

It also carries a common-identity header with final fitted scale and an
A-planning identity digest derived from the shared theta mode, ratio, limits,
resolver, smoothing, hold, wrap, and row-order settings. Every file must declare
the same G54 frame centre, compensation profile, compensation and pen-radius
reserves, planning radius, final fitted scale, and A-planning identity. Wave
row-locked files retain their per-ink screen-angle identity as a separate check.

The registration audit:

1. Parses the final `G1` machine points between each named mark's `M3` and `M5`.
2. Divides emitted motor-shaft `A` by the file's theta-ratio identity.
3. Inverts the selected compensation transform to recover bed-frame points.
4. Combines each horizontal/vertical arm midpoint into one mark centre.
5. Removes the declared pen offset and compares matched IDs against cyan.
6. Checks translation, rotation, scale, RMS, maximum residual, and exact
   single application of each pen offset.
7. Requires at least four non-collinear mark IDs and identical ID sets in every
   selected ink.

The software maximum-residual limit is `0.10 mm`; RMS limit is `0.05 mm`.
`0.10 mm` is 11 % of the current `0.90 mm` pen, half the `0.20 mm` calibration
pen, and stricter than the approximately `0.218 mm` RMS / `0.591 mm` maximum
measured residual of the verified physical compensation field. It is therefore
a command-geometry invariant rather than a claim about paper. Translation and
the transform tolerances are derived from that same `0.10 mm` at the measured
corner radius.

Save runs this audit on planned program text before any target file is written.
After transaction-style export, it re-reads all files from disk and runs the
audit again. A pre-write failure writes nothing. A post-write failure leaves the
files for diagnosis, marks the save as failed, and must not report a successful
CMYK release. The overlay JSON and version-6 set manifest record each ink's
matched count, centroid, translation, rotation, scale, RMS, maximum residual,
pen-offset error, and pass/fail state. The PNG adds mark centres and residual
vectors.

## Consequences

- A missing, duplicated, translated, rotated, or scaled registration pattern
  blocks the CMYK set instead of producing a misleading identity-only PASS.
- Corner crosses are enabled by default and are now required release geometry
  for CMYK artwork. Calibration sheets keep their own fiducial workflow.
- The audit uses the selected profile and row angle to reverse the same
  compensation transform that the planner applied. Header identity alone is
  not accepted as pointwise evidence.
- Set manifests advance to version 6. Older manifests remain historical
  records; they do not satisfy the new release gate.
- The software threshold is deliberately tighter than the machine's measured
  physical residual. Passing it means the G-code commands agree geometrically;
  it does not prove pen-tip alignment, paper movement, bed flatness, contact
  pressure, ink spread, or final optical overlay.
- A physical four-file run after one `G65 P113` HOME + REGISTER, with no sheet
  shift or re-registration between passes, remains required.

## Verification

- A red regression first showed the old audit reporting PASS with cyan shifted
  `10 mm`; the new audit rejects that set.
- Matching fixed-bed and rotating-bed sets recover all four mark centres and
  pass after compensation inversion.
- Regressions reject a whole-program translation, `0.10 deg` rotation,
  `0.1 %` scale, changed mark IDs/counts, and a pen offset applied twice.
- A genuine single `0.75,-0.20 mm` pen offset passes and its configured value
  must match the emitted metadata.
- Save integration proves the preflight failure occurs before export and a
  post-write file corruption prevents the successful-save status.
- Complete converter discovery passes with one expected OpenGL-context skip.

## Physical follow-up

Generate four fresh files from this commit or later with registration crosses
enabled, run `G65 P113` once, then run cyan, magenta, yellow, and black on one
sheet without changing G54, the sheet, or registration. Compare the four
printed crosses and photo-measure the residual; the current expected starting
case is XY-only before repeating under rotating-bed planning.
