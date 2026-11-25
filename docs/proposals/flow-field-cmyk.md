# Implemented feature: Flow-Field CMYK (structure-tensor streamline hatching)

**Status:** Implemented as the CMYK **Edge-flow streamlines** screen. Current
behavior and the software-selected recipe are in
[`../../software/README.md`](../../software/README.md); the current change
record is `WSW-20261125-004`.

## Intent
Add an optional CMYK rendering mode to the converter that replaces fixed-angle
hatch patterns with smooth vector-field-guided streamlines following image
contours and forms. The recommended photo action now selects **Coherent color
flow**, which owns one shared streamline geometry per density layer and assigns
contiguous local ink planes along it. The prior per-ink and stochastic shared
Edge-flow modes remain available for comparison. Preserve the existing four-file
CMYK output, page-registration, preview, and G-code contracts.

## Proposed processing
1. Load raster artwork and derive CMYK channel coverage values using the converter's existing color-separation conventions.
2. Compute gradients across scene luminance and the separated C/M/Y/K tone
   maps. Construct a local multichannel structure tensor from each channel's
   `Ix², IxIy, Iy²` terms and Gaussian-smooth the summed components.
3. Extract a tangent direction (minor-eigenvalue eigenvector) to follow edges/forms; estimate directional coherence from eigenvalues. Treat directions as **unoriented** (theta equivalent to theta + pi) to avoid streamline flips.
4. Smooth the direction field and blend toward each plate's fixed fallback
   angle where structure is weak/ambiguous. Moderate coherent gradients retain
   the shared image-form direction; only near-flat or incoherent texture falls
   back. Avoid abrupt transitions and let the form continue across temporary
   single-ink tone gaps.
5. Trace streamlines with stable numerical integration, seed distribution,
   minimum-distance/collision checks, bounds clipping, and curvature limits.
   Start from the operator's base pitch, then continuously shorten the
   neighbour-to-neighbour pitch as local ink tone darkens. Clamp the result to
   a pen-safe minimum.
6. In coherent color flow, trace one shared geometry per density layer. Along
   each path, smooth every channel's coverage over paper-space arc length and
   keep a dominant ink plus one close secondary ink. Tone changes therefore
   follow long local color planes instead of independent per-channel random
   intervals. Additional layers add offset parallel geometry only in darker
   regions.
6a. Apply a self-guided edge-preserving simplification before sharpening and
    separation. This reduces pores, sensor texture, and fine fabric noise
    without moving strong eyes, glasses, silhouettes, or plaid boundaries.
6b. Boost Black only where tensor guidance confidence is high, and reduce
    ordinary Black weight while keylines are active. Weak image structure
    falls back to the cyan 15°, magenta 75°, yellow 0°, and black 45° family
    across successive layers.
6c. Retain the legacy per-ink renderer and the explicitly labeled
    stochastic shared-network renderer for comparison. Both still save four
    page-registered programs.
7. Emit continuous, stroke-only SVG centerlines compatible with the existing SVG-to-G-code path (no fills, text, or defs); retain units, coordinate mapping, and pen-change/channel separation.

## Current controls (software-selected starting values)
- Rendering mode: **Coherent color flow (shared geometry, ink planes)** from
  **Use recommended photo defaults**; the prior Edge-flow modes remain
  selectable in the CMYK Screen style
- Base line spacing: operator-owned Edge-flow pitch and artwork scale; Auto
  does not change either. The recommended photo action targets two pen widths
  on paper with a `1.2 mm` minimum pitch.
- Tensor smoothing radius: `2.5 mm` on paper for the recommended photo recipe
- Guidance gate: tensor strength plus coherence across luminance and C/M/Y/K
  tone gradients; moderate structure keeps the shared image direction
- Fallback direction: each ink's own fixed screen angle only where structure is
  weak or ambiguous
- Shade compression: `60 %` for the recommended photo recipe; at
  full local tone the target spacing is `40 %` of Dot pitch, bounded at
  `0.9` pen widths
- Maximum density layers: 3 for the recommended photo recipe
- Tone method: contiguous smoothed ink planes along a common geometry network.
  A 6 mm paper-space coverage window keeps long runs; a second ink is retained
  when it reaches `72 %` of the dominant coverage. Additional layers add
  offset parallel geometry in darker regions instead of random short
  fragments.
- Embedded ICC profiles, including Display P3, are converted to sRGB before
  image analysis and separation; EXIF orientation is applied first
- **Pen-down chain** bridges up to `4 mm` of coverage gaps along one coherent
  shared path, then chains adjacent marks within the operator's gap. The
  recommended photo action limits that adjacent gap to `1.0 mm`; its
  connectors add visible local ink but cannot cross several screen rows.
- **Continuous row screen (adjacent joins)** is a speed-oriented alternative:
  tone-pitch rows join nearest non-overlapping adjacent runs into a few long
  chains, accepting visible straight connectors in exchange for fewer M3/M5
  cycles
- Auto starts from the portrait detail curve, then selects the lowest
  predicted process-ink colour error inside an exposure-preserving Edge-flow
  window: brightness `100-140 %`, contrast `120-180 %`, saturation
  `105-120 %`, gamma `1.00-1.30`, and GCR `60-80 %`. All four ink weights
  reset to 100 %. The estimate remains a coverage-model RGB error, not a
  paper-validated colour claim.
- Legacy per-ink Fine-detail preset: one effective pen width, smoothing near
  two pen widths
  clamped to `1.0-1.5 mm`, five low-offset layers, `65 %` continuous pitch
  compression, `2 mm` path-local tone intervals, marks capped near `12 mm`,
  and Path tolerance no larger than `0.10 mm`
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
- Default program menus still expose the prior per-ink and stochastic shared
  methods, while **Use recommended photo defaults** selects coherent color
  flow. All modes save four independently screened G-code programs.
- Long coherent paths retain contiguous local ink planes; dark regions add
  offset geometry and flat regions retain a fixed-angle screen.
- Coherent local ink runs and adjacent per-ink marks are chained only within
  the operator's visible-ink and pen-down limits.
- Deterministic results for fixed settings/seed; no infinite tracing loops; reasonable bounds on output size and runtime.

## Source idea
User-provided description of a Reddit artist's method: image gradients -> blurred structure tensor -> smooth edge-following direction field -> evenly spaced streamlines -> extra layers in dark regions -> fixed-angle fallback where structure is unclear.

Physical four-pass validation, final pitch, smoothing, layer count, and pen
order remain pending.
