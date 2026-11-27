# ADR-015: Separate Wave fidelity tone density from local contrast amplitude

- Status: accepted and implemented
- Date: 2026-11-27

## Context

The production Variable-depth Wave mode kept one continuous stroke on every
candidate row at a common baseline pitch. With a `0.90 mm` pen and a final
pitch near `1.26 mm`, one row contributes roughly 70% area coverage before
waveform curvature. Pen-plus-edge clearance limits how much independent row
motion can increase or decrease that coverage. The continuous screen therefore
has a narrow density range even when separation and waveform shape are
correct. On the owner's portrait, the corrected software separation had a
suitable target CMYK range while the screened composite remained substantially
too dark, and local ink coverage correlated poorly with the requested tone.

Transparent source pixels and the nominal process-ink response were also not
shared consistently through image preparation, separation, and preview. A
transparent PNG could become a false black field, and the solver could target
a different ink model from the renderer.

## Decision

CMYK image preparation composites transparency over paper white, applies EXIF
orientation, and converts valid embedded ICC profiles to sRGB before tone
analysis. CMYK separation solves against the same nominal or measured
process-ink multiply model used by the shared preview.

Add a separate production style,
**Variable-depth Wave - fidelity (tone density)** (`waves_fidelity`). It
separates absolute ink quantity from immediate image contrast:

- Candidate rows remain on the uniform baseline lattice
  `y_i = y0 + i * pitch`.
- A deterministic ordered threshold keyed by ink seed and row index controls
  whether each row's locally smoothed channel coverage is emitted.
- Light areas can therefore use density below the continuous one-row floor;
  dark areas retain every row.
- Immediate adjacent scene-luminance differences drive waveform amplitude.
  The response is not spatially smoothed and has no nonzero amplitude floor:
  uniform areas stay on their baselines, while a narrow dark/light edge
  creates a correspondingly narrow amplitude spike.
- The contrast sample includes one source pixel on either side of each carrier
  sample, so a one-pixel edge cannot disappear between normal output samples.
  A small dead band suppresses compression or paper-texture noise.
- Absolute per-ink coverage still controls row density. It is not reused as
  the fidelity amplitude signal.
- Coarse cells whose adjacent scene contrast is at least `38 %` retain
  alternating rows across that cell and its immediate neighbours. This local
  row thinning gives a sharp amplitude spike enough physical room that the
  pen-plus-edge envelope does not globally flatten the complete image.
- All emitted rows keep the shared phase carrier and slope-aware amplitude
  envelope.
- The final shortest-segment pen-plus-edge clearance check remains
  authoritative.
- Existing `waves_fixed`, `waves_even`, and diagnostic recipes retain their
  prior behavior.

The set manifest records fixed-baseline tone-density semantics, and the final
coordinate checker accepts legitimate missing row indices while proving that
all emitted baselines remain on the declared uniform grid.

## Consequences

- Wave fidelity is no longer limited to the coverage range of one continuous
  stroke per row.
- Skipped rows remain physically separated by one or more whole pitches, so
  density control cannot create a new collision case.
- Ink coverage becomes spatially discontinuous at row scale. The fidelity mode
  is a photo workflow, not a claim that every row has an equal visible gap.
- Edge contrast and broad tone now have separate representation. A uniform
  dark field is flat at the waveform level and depends on row density for its
  ink quantity; a strong edge receives a local amplitude spike.
- Strong edges use roughly half the candidate rows in their local contrast
  cells. This is a deliberate coverage/definition tradeoff: it buys visible
  wave height at the live `1.265 mm` pitch, where retaining every adjacent row
  leaves only `0.095 mm` nominal row-gap headroom.
- Tone-density row gaps increase M3/M5 fragmentation relative to a continuous
  row when light regions alternate. The exact program cost must be measured
  for the selected source and pitch.
- The software composite can approach the source more closely, but physical
  felt-tip bleed, pressure, paper absorption, registration, and machine
  following error remain outside the model.

## Verification

- Red-capable oracle tests cover source detail, CIELAB/chroma/hue error,
  per-ink coverage correlation and bias, Wave amplitude/cycles/interior
  variation, depth sensitivity, and G-code row evidence.
- Focused fidelity geometry tests verify density selection, fixed-grid
  baselines, shared phase, all four screen angles, shortest-segment clearance,
  flat uniform tone, monotone contrast-spike height, one-pixel edge
  preservation, and a live-pitch edge above `0.45 mm` median peak-to-peak.
- A real four-ink save passes the final baseline/clearance checker.
- At the saved live recipe, median row peak-to-peak rises from `0.144 mm` to
  `0.485 mm`; the sidecar oracle's worst sampled region rises to `0.576 mm`
  and now clears its `0.50 mm` amplitude gate.
- The live failed recipe remains a red fidelity baseline; the fidelity mode
  clears the Wave-persistence/amplitude checks, while color, coverage, and
  structure limits are reported rather than hidden.

## Related records

- `WSW-20261127-004`
- `WSW-20261127-005`
- `WSW-20261127-006`
- `WSW-20261127-007`
- ADR-009
- ADR-014
