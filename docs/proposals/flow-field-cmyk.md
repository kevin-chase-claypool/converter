# Implemented feature: Flow-Field CMYK (structure-tensor streamline hatching)

**Status:** Implemented as the CMYK **Edge-flow streamlines** screen. Current
behavior and the software-selected recipe are in
[`../../software/README.md`](../../software/README.md); the current change
record is `WSW-20261123-001`.

## Intent
Add an optional CMYK rendering mode to the converter that replaces fixed-angle hatch patterns with smooth vector-field-guided streamlines following image contours and forms. Preserve the current CMYK method and all existing output behavior by default.

## Proposed processing
1. Load raster artwork and derive CMYK channel coverage values using the converter's existing color-separation conventions.
2. Compute image luminance gradients (Ix, Iy). Construct a local structure tensor from Ix², IxIy, Iy² and Gaussian-smooth its components.
3. Extract a tangent direction (minor-eigenvalue eigenvector) to follow edges/forms; estimate directional coherence from eigenvalues. Treat directions as **unoriented** (theta equivalent to theta + pi) to avoid streamline flips.
4. Smooth the direction field and blend toward a configurable fixed fallback angle where structure is weak/ambiguous. Guard low-gradient regions and avoid abrupt transitions.
5. Trace evenly spaced streamlines using stable numerical integration, seed distribution, minimum-distance/collision checks, bounds clipping, and curvature limits. Modulate the visible fraction of each path with local channel tone instead of switching whole-face density bands.
6. Build one strength-gated luminance direction field for image form. Give each CMYK plate its own coverage mask, seed, continuous tone fraction, extra shadow layers, and classic fallback screen angle. Save four separate, page-registered programs so they overlap as four physical pen passes.
7. Emit continuous, stroke-only SVG centerlines compatible with the existing SVG-to-G-code path (no fills, text, or defs); retain units, coordinate mapping, and pen-change/channel separation.

## Current controls (software-selected starting values)
- Rendering mode: **Edge-flow streamlines** in the existing CMYK Screen style
- Base line spacing: `0.8 mm` source pitch / `1.2 mm` effective at 150 % scale
- Tensor smoothing radius: `2.0 mm` on paper
- Guidance gate: tensor strength plus coherence; weak structure keeps screen
- Fallback direction: cyan 15, magenta 75, yellow 0, black 45 degrees
- Maximum density layers: 3
- Tone method: deterministic path-local `4-8 mm` ink segments, with extra
  layers for darker coverage and no shared 2D block lattice
- Optional preview of each channel and composite

## Implementation plan
- Inspect current CMYK UI, raster processing, SVG generation, and XY-Theta G-code constraints before choosing integration points.
- Prototype monochrome structure-guided streamlines first; test portraits, landscapes, smooth gradients, flat backgrounds, and sharp geometric edges.
- Extend to CMYK channels with independent coverage and registration checks.
- Compare runtime, SVG path count, pen lifts, overlap, total path length, and visual quality against the existing mode.
- Add regression tests confirming the existing CMYK output is unchanged unless Flow-Field CMYK is explicitly selected.

## Acceptance criteria
- Existing CMYK workflow remains the default and unaffected.
- New mode produces valid continuous stroke-only SVG paths and runs through the current converter without special G-code handling.
- Lines visibly follow coherent image structures; weak-structure regions use a stable fallback direction.
- Darker channel regions produce greater appropriate ink coverage without pathological overplotting.
- Deterministic results for fixed settings/seed; no infinite tracing loops; reasonable bounds on output size and runtime.

## Source idea
User-provided description of a Reddit artist's method: image gradients -> blurred structure tensor -> smooth edge-following direction field -> evenly spaced streamlines -> extra layers in dark regions -> fixed-angle fallback where structure is unclear.

Physical four-pass validation, final pitch, smoothing, layer count, and pen
order remain pending.
