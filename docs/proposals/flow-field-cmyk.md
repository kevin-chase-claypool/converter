# Implemented feature: Flow-Field CMYK (structure-tensor streamline hatching)

**Status:** Implemented as the CMYK **Edge-flow streamlines** screen. Current
behavior and the software-selected recipe are in
[`../../software/README.md`](../../software/README.md); the current change
record is `WSW-20261123-019`.

## Intent
Add an optional CMYK rendering mode to the converter that replaces fixed-angle hatch patterns with smooth vector-field-guided streamlines following image contours and forms. Preserve the current CMYK method and all existing output behavior by default.

## Proposed processing
1. Load raster artwork and derive CMYK channel coverage values using the converter's existing color-separation conventions.
2. Compute image luminance gradients (Ix, Iy). Construct a local structure tensor from Ix², IxIy, Iy² and Gaussian-smooth its components.
3. Extract a tangent direction (minor-eigenvalue eigenvector) to follow edges/forms; estimate directional coherence from eigenvalues. Treat directions as **unoriented** (theta equivalent to theta + pi) to avoid streamline flips.
4. Smooth the direction field and blend toward a configurable fixed fallback angle where structure is weak/ambiguous. Guard low-gradient regions and avoid abrupt transitions.
5. Trace evenly spaced streamlines using stable numerical integration, seed distribution, minimum-distance/collision checks, bounds clipping, and curvature limits. Modulate the visible fraction of each path with local channel tone instead of switching whole-face density bands.
6. Build one strength-gated luminance direction field, then trace four
   independently seeded and fallback-angled streamline networks, one for each
   CMYK plate. Apply each ink's own tone mask, dark-tone layers, and optional
   keyline adjustment, then save four separate page-registered G-code
   programs.
6a. Retain one explicitly labeled experimental shared-network renderer for
    comparison. Its independent phases and normalized occupancy prevent the
    correlated four-ink black runs that made the first shared prototype
    unusable.
7. Emit continuous, stroke-only SVG centerlines compatible with the existing SVG-to-G-code path (no fills, text, or defs); retain units, coordinate mapping, and pen-change/channel separation.

## Current controls (software-selected starting values)
- Rendering mode: **Edge-flow streamlines** in the existing CMYK Screen style
- Base line spacing: operator-owned Edge-flow pitch and artwork scale; Auto
  does not change either
- Tensor smoothing radius: `4.0 mm` on paper for the current portrait recipe
- Guidance gate: tensor strength plus coherence; weak structure keeps screen
- Fallback direction: each ink's own fixed screen angle where structure is weak
- Maximum density layers: 5 for the current portrait recipe
- Tone method: deterministic path-local ink segments on four independent
  networks; additional layers add local depth only on the darker plate, and
  there is no shared 2D block lattice
- Embedded ICC profiles, including Display P3, are converted to sRGB before
  image analysis and separation; EXIF orientation is applied first
- **Pen-down chain** bridges up to `4 mm` of tone-off gaps along each
  individual streamline and also chains per-ink marks within the operator's
  adjacent gap. The connectors add visible local ink but materially reduce
  M3/M5 cycles.
- **Continuous row screen (adjacent joins)** is a speed-oriented alternative:
  tone-pitch rows join nearest non-overlapping adjacent runs into a few long
  chains, accepting visible straight connectors in exchange for fewer M3/M5
  cycles
- Auto now starts from the portrait detail curve, then selects the lowest
  predicted process-ink colour error across Auto levels, brightness, contrast,
  saturation, GCR, and gamma. All four ink weights reset to 100 %. For the
  current portrait and `0.52 mm` effective pitch the result is Auto levels off,
  brightness 80 %, contrast 260 %, saturation 90 %, GCR 90 %, gamma 0.60,
  with a coverage RGB estimate of `32.8/255`. The earlier `4.7/255` figure was
  a coverage-only claim and is retired.
- Fine-detail preset: one effective pen width, smoothing near two pen widths
  clamped to `1.0-1.5 mm`, five low-offset layers, `2 mm` path-local tone
  intervals, marks capped near `12 mm`, and Path tolerance no larger
  than `0.10 mm`
- Fine detail reports a checked/`✓` state only while every preset control
  still matches; manual edits clear it
- Fine detail is reversible: activation saves the prior edge-flow layout, and
  deactivation restores it and clears the checkmark
- Optional Continuous Black keylines with edge separation: preserve
  high-coherence boundaries in Black and reduce C/M/Y coverage beside them
- Fine detail sharpening: 60 %, 1.5 mm unsharp mask on the photo luminance
- Optional preview of each channel and composite

## Implementation plan
- Inspect current CMYK UI, raster processing, SVG generation, and XY-Theta G-code constraints before choosing integration points.
- Prototype monochrome structure-guided streamlines first; test portraits, landscapes, smooth gradients, flat backgrounds, and sharp geometric edges.
- Extend to CMYK channels with four independent pen networks and registration
  checks, while keeping any co-located experiment explicit.
- Compare runtime, SVG path count, pen lifts, overlap, total path length, and visual quality against the existing mode.
- Add regression tests confirming the existing CMYK output is unchanged unless Flow-Field CMYK is explicitly selected.

## Acceptance criteria
- Existing CMYK workflow remains the default and unaffected.
- Embedded wide-gamut image profiles are converted to sRGB before CMYK
  separation, with EXIF orientation preserved.
- New mode produces valid continuous stroke-only SVG paths and runs through the current converter without special G-code handling.
- Lines visibly follow coherent image structures; weak-structure regions use a stable fallback direction.
- Darker channel regions produce greater appropriate ink coverage without pathological overplotting.
- Default Edge-flow produces four distinct per-ink path networks and saves four
  independently screened G-code programs.
- Adjacent per-ink marks are chained when their gap is within the operator's
  pen-down limit.
- Deterministic results for fixed settings/seed; no infinite tracing loops; reasonable bounds on output size and runtime.

## Source idea
User-provided description of a Reddit artist's method: image gradients -> blurred structure tensor -> smooth edge-following direction field -> evenly spaced streamlines -> extra layers in dark regions -> fixed-angle fallback where structure is unclear.

Physical four-pass validation, final pitch, smoothing, layer count, and pen
order remain pending.
