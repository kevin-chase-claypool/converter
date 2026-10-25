# Wave-row zero points and adjacent-row clearance in open-source generators

**Date:** 2026-10-24

## Question

Each wave row has a zero point where its sine displacement returns to the row
baseline. Should the generator use those zero points to keep rows equidistant,
and how do established open-source plotter wave generators handle this?

## Conclusion

The major implementations do reset each row's phase to zero and retain a fixed
row baseline. That confirms the zero-point model. They do **not**, however,
provide a general guarantee that neighboring rows remain equidistant or
collision-free throughout the image.

The common approach is:

1. Set equally spaced row baselines.
2. Reset phase to zero at the start of every row.
3. Drive wave amplitude and phase increment from image brightness.
4. Limit frequency relative to pen/stroke width to avoid overcrowding within a
   row.
5. Rely on sensible amplitude limits; no reviewed implementation performs a
   general nearest-distance check between adjacent rows.

This means their default appearance usually looks clean, but the user can
still choose amplitude/frequency combinations that cross neighboring rows.

## Primary-source evidence

### SquiggleDraw

- In the row loop, the sketch resets `a = 0.0` for every row:
  [SquiggleDraw.pde, row setup](https://github.com/gwygonik/SquiggleDraw/blob/2d2131d7807ac96f9145e23c0f0e64bce72471a5/SquiggleDraw/SquiggleDraw.pde#L256-L272).
- A separate `phase = 0.0` is also initialized inside every row before samples
  are generated:
  [wave generation](https://github.com/gwygonik/SquiggleDraw/blob/2d2131d7807ac96f9145e23c0f0e64bce72471a5/SquiggleDraw/SquiggleDraw.pde#L345-L347).
- Brightness drives both amplitude and phase increment:
  [tone formulas](https://github.com/gwygonik/SquiggleDraw/blob/2d2131d7807ac96f9145e23c0f0e64bce72471a5/SquiggleDraw/SquiggleDraw.pde#L368-L395).
- Output is positioned around the fixed row coordinate `y`:
  [point construction](https://github.com/gwygonik/SquiggleDraw/blob/2d2131d7807ac96f9145e23c0f0e64bce72471a5/SquiggleDraw/SquiggleDraw.pde#L424-L432).
- A major rendering rewrite capped phase increment according to stroke width
  because crests closer than the pen width only add ink and plotting time:
  [SquiggleDraw PR #12](https://github.com/gwygonik/SquiggleDraw/pull/12).
- A row-direction defect was fixed by calculating each row's geometry first
  and only then reversing the point array. The author explicitly says rows are
  calculated identically whether reversed or not:
  [issue #14](https://github.com/gwygonik/SquiggleDraw/issues/14),
  [PR #16](https://github.com/gwygonik/SquiggleDraw/pull/16).

### SquiggleCam

- The row loop resets `a = 0` and starts at `[0, y]`, so every row begins at
  its baseline/zero point:
  [App.vue, row initialisation](https://github.com/msurguy/SquiggleCam/blob/b33aab5c6e5b5176853245c67f18b0e862f252f0/src/App.vue#L380-L383).
- Image brightness changes both amplitude (`r`) and accumulated phase (`a`);
  the output is `y + sin(a) * r`:
  [App.vue, waveform](https://github.com/msurguy/SquiggleCam/blob/b33aab5c6e5b5176853245c67f18b0e862f252f0/src/App.vue#L412-L416).

### Plotterfun

- `squiggle.js` uses the same row-local `a = 0`, `r = amplitude * z /
  lineCount`, and `a += z / frequency` structure:
  [squiggle.js](https://github.com/mitxela/plotterfun/blob/faf67d4dadc359a9d5703b0c4e501ea3bbad84d9/squiggle.js#L25-L33).
- Its left/right variant also resets phase per row, starts each row at the
  baseline, alternates traversal direction, and emits `sin(a) * r`:
  [squiggleLeftRight.js](https://github.com/mitxela/plotterfun/blob/faf67d4dadc359a9d5703b0c4e501ea3bbad84d9/squiggleLeftRight.js#L29-L45).

### SquiggleDraw for Inkscape

- This is the closest open-source CMYK prior art. Each row begins with an SVG
  move to its baseline, while `bidi` rows are reversed and their amplitude is
  negated so the same physical curve is retained:
  [squiggledraw.py, row loop](https://github.com/gwygonik/SquiggleDrawInkscape/blob/96773a6e75430063ddba1af846dec1e70feba4ff/squiggledraw.py#L229-L259).
- Its README explicitly supports CMY(K) layers:
  [README](https://github.com/gwygonik/SquiggleDrawInkscape/blob/d6605b132e09d835da4cc35e26e457f29273bf89/README.md).
- The source has no adjacent-row clearance or collision-avoidance pass.

## What this means for the Theta converter

The zero-point idea is correct but is only an anchor, not a complete invariant:

- At a shared zero crossing, equal row baselines guarantee the nominal pitch.
- Between zero crossings, independent amplitude or frequency changes can still
  move neighboring rows closer.
- Shared phase and wavelength make every row parallel; this is the strictest
  interpretation and guarantees constant separation.
- Per-row frequency is required for the richer low/high-frequency depth seen in
  SquiggleDraw-style output, but even the reviewed open-source implementations
  do not guarantee that this remains collision-free.

The open-source projects therefore confirm the artistic technique but do not
provide an algorithm that simultaneously guarantees:

1. independent per-row low/high-frequency modulation,
2. exact row spacing at all horizontal positions, and
3. no adjacent-row contact.

## Recommended next experiment

Build a **zero-anchored variable wave** variant that:

- starts every row at phase zero on the same vertical grid;
- keeps the fundamental waveform phase locked at shared zero points;
- adds bounded per-row harmonic/frequency variation for depth;
- rejects or damps the variation wherever a sampled minimum-clearance check
  would bring two inked centerlines closer than `pen_width + gap_margin`;
- verifies both ideal-tone patches and the real Ben1 image at all four CMYK
  angles.

This preserves the useful depth behavior observed in the open-source tools while
adding the missing clearance guarantee that those tools leave to manual tuning.

## Method and limitations

- Sources were read directly from the repositories through the GitHub API on
  2026-10-24 at the commit revisions linked above.
- The review covers the main SquiggleDraw implementation, its native Inkscape
  CMYK rewrite, SquiggleCam, and Plotterfun. It is not an exhaustive survey of
  every fork or private implementation.
- No physical print comparison was performed for these external tools.
