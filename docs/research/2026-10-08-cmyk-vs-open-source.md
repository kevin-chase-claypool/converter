# CMYK: this converter vs the best open-source references

Date: 2026-10-08

Question: how does this repository's CMYK feature compare with the strongest
open CMYK raster-to-plot tools, and what is worth improving?

## Sources read (primary)

- ohnorobo/cmyk-splitter (MIT): `backend/services/cmyk_splitter.py` (read
  2026-10-07), `halftone_dots.py` and `svg_combiner.py` (read 2026-10-08).
  The separation math this repository ported.
- ClayFlannigan/halftone (Apache-2.0): `halftone.py` (read 2026-10-08). The
  most complete open CMYK separation + halftone screener with GCR and screen
  angle controls.
- SonarSonic/DrawingBotV3 (GPL-3.0 free; CMYK is premium/closed):
  `docs/source/cmyk.rst` (read 2026-10-08). The community's quality
  reference; docs only, no code.
- serycjon/vpype-flow-imager (GPL-3.0): README `--cmyk` section (read
  2026-10-08). External CLI path.
- svenhb/plotterfun-color (MIT): `main.htm` (read 2026-10-08). Per-channel
  application of the 22 algorithms, four SVG path groups.
- ehufsted/HalftoneWebPAL (GPL-3.0): `index.html` (read 2026-10-08). An
  "CMYK - 4 layers" ink mode option.

Source URLs:
https://github.com/ohnorobo/cmyk-splitter ,
https://github.com/ClayFlannigan/halftone ,
https://drawingbotv3.readthedocs.io/en/latest/cmyk.html ,
https://github.com/serycjon/vpype-flow-imager ,
https://github.com/svenhb/plotterfun-color ,
https://github.com/ehufsted/HalftoneWebPAL

## Where this implementation already matches or exceeds them

1. Separation math: the same GCR core as cmyk-splitter and ClayFlannigan
   (`k = min(cmy) * gcr`, CMY rescaled) in `rgb_to_cmyk_tone`
   (`software/converter_core/cmyk.py:76`), plus per-ink weights, gamma,
   saturation/contrast/brightness, and a photo Auto button
   (`software/generator_tabs/cmyk_tab.py:152`) that none of the references
   match - DrawingBotV3's CMYK dialog applies fixed recommended settings.
2. Screen angles: classic C 15 / M 75 / Y 0 / K 45
   (`software/converter_core/cmyk.py:37`), identical to
   ClayFlannigan/halftone's default `[15, 75, 0, 45]`. cmyk-splitter has no
   angles at all; its dot plotter randomly samples pixel coordinates.
3. Mark vocabulary: nine screen styles including the joined-row rectilinear
   serpentine with a 7x light-tone stretch
   (`software/converter_core/cmyk.py:669-678`). DrawingBotV3 instead runs its
   full path-finding modules per channel; our flow-field work lives in other
   tabs, not in a CMYK screen style.
4. Preview mixing: our Ink simulation multiplies pen-width strokes over
   paper. The references agree with the model - cmyk-splitter sets
   `style="mix-blend-mode: multiply"` on every layer group in its combined
   SVG, ClayFlannigan's preview uses `(1 - C)(1 - K)` (its `cmyk_to_rgb`),
   and DrawingBotV3 activates a "Darken" blend mode for its CMYK viewer.
   We exceed all three with live layer toggles, real pen-width strokes, and
   per-ink M3 counts.
5. Per-ink balance: DrawingBotV3 tells users to "change the multiplier for
   each pen" after an initial plot; our per-ink weights plus the Auto button
   cover the same ground, driven by the actual image.
6. Machine output and calibration: none of the references emit machine
   G-code. We run the r-theta cost solver and the M3/M5 contract per ink, and
   `tools/cmyk_calibrate.py` (`fit_profile`) turns a plotted sheet into
   measured ink transmittances plus a multiply validation - unique in this
   survey.

## Gaps worth closing (each tied to the evidence)

1. Measured profile not yet loaded into the simulation. The sheet and
   analyzer exist (`docs/testing/CMYK_CALIBRATION.md`), but Ink simulation
   still multiplies display colours. DrawingBotV3's own manual concedes its
   viewer "may differ from the final plot" and asks for experimentation;
   measured inks close exactly that gap.
2. Exported SVGs do not blend. Our layer SVGs render opaquely in Inkscape.
   cmyk-splitter's combiner sets `mix-blend-mode: multiply` per layer; adding
   the same attribute makes external previews match our simulation.
3. No registration aids in art mode. The calibration sheet has fiducials,
   but a normal four-pass job has nothing to verify pass alignment - the
   community's top failure mode per the 2026-10-07 prior-art survey.
   Optional corner crosses drawn by all inks plus a pass-order note would
   cover it.
4. Pen-width/pitch coupling is manual. DrawingBotV3's CMYK notes recommend
   setting the drawing area and enabling "Rescale to Pen Width"; our
   pitch/scale/pen-width relationship lives only in tooltips and defaults.
   A "match pen width" helper would prevent the coverage-floor and tonal
   range traps we debugged on 2026-10-08.
5. No flow-field-style screen. DrawingBotV3 runs any path-finding module per
   channel; our nearest styles are the line and rectilinear screens. The
   repository already has a flow-field generator that could be exposed as a
   CMYK screen style.
6. Preview multipliers are internal. DrawingBotV3 exposes per-pen
   multipliers as UI; after (1) lands, exposing the measured ink values as
   editable sliders keeps the print loop one click deep.

## Ranked top improvements

1. Load the measured calibration profile into Ink simulation (finishes the
   loop this repository already built).
2. Set `mix-blend-mode: multiply` on exported layer/combined SVGs (external
   preview parity, one attribute).
3. Optional registration crosses and a pass-order note in art mode (the
   community's top failure mode).
4. A "match pen width" pitch helper (prevents coverage-floor and tonal-range
   mistakes).
5. Flow-field hatch as a CMYK screen style (DrawingBotV3 PFM parity).
6. Expose measured per-ink multipliers as editable UI after calibration.

## Caveats

- DrawingBotV3's CMYK feature is premium and closed; only its public docs
  were used, as a quality reference.
- plotterfun-color and HalftoneWebPAL were verified for their CMYK mode only;
  their algorithms were not executed here and their full option sets were
  not audited.
