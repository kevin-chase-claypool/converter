---
id: WSW-20261029-008
date: 2026-10-29
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
  - samples/gcode/Ben2/PXL_20201128_211515508-cmyk-cyan-equidistant.gcode
  - samples/gcode/Ben2/PXL_20201128_211515508-cmyk-magenta-equidistant.gcode
  - samples/gcode/Ben2/PXL_20201128_211515508-cmyk-yellow-equidistant.gcode
  - samples/gcode/Ben2/PXL_20201128_211515508-cmyk-black-equidistant.gcode
  - samples/gcode/Ben2/PXL_20201128_211515508-cmyk-equidistant-set.json
  - docs/report/lab-notes/2026-10-29-ben2-yellow-row-spacing-classification.md
tags:
  - cmyk
  - wave-screen
  - row-spacing
  - phase-locked
  - manifest
  - ben2
related:
  - WSW-20261024-011
  - WSW-20261026-001
---

# Clarify variable-depth wave spacing

## Summary

The phase-locked Wave-screen option is now labelled **Wave screen -
phase-locked, variable depth**. Its tooltip states that row-specific amplitude
changes instantaneous row spacing even though crests remain aligned. Set
manifests now record the actual wave layout instead of labelling every screen
style as shared-zero-anchored.

## Reason

The Ben2 yellow file was generated with `waves_zero` while the print was being
evaluated for exact row pitch. Decoding its commanded X/Y/A path back through
the same bed rotation and compensation transformed the saved file into paper
coordinates: its adjacent gaps ranged from `1.791` to `2.049 mm`. The
regenerated `waves_even` file held a nominal `1.91546 mm` gap across the page.
The unequal gaps were therefore already present in the program, rather than
being introduced only by the bed rotation.

## Implementation

- Display `waves_zero` as **Wave screen - phase-locked, variable depth**.
- Explain in the style tooltip that shared crest phase does not imply constant
  row pitch when each row has a different amplitude.
- Record `wave_phase_mode` as `identical_translated_rows` for `waves_even`,
  `shared_zero_anchored` for `waves_zero`, `bounded_row_depth` for `waves`, and
  `null` for non-wave styles.
- Add a regression that measures the changing centreline gap in the
  phase-locked variable-depth mode.

## Verification

- Source image SHA-256:
  `DDD4D5BA8FFB54BF5063039B15659A05D01628E7F82977B1F2D4DD7EF27068B2`.
- Original yellow G-code SHA-256:
  `DA4826610832ED83EB774A721F6B9A8B08812C83E04E182F650E61A2F403F894`.
- Corrected equidistant G-code SHA-256:
  cyan `2088D6FB4B18CB706D6A2F64DE84CB9DC34F0BBB574D629AF9DF87D38566CC22`,
  magenta `45AC9C7E0F1230768DCA36700C36A3F4770E61E5217DED71A837EC29635AF324`,
  yellow `4BDE0728D6273F73CBA10159B210C8FE810202CFC2B3F4333B0B6E63EBCCCABD`,
  black `8388D4E82489BA863EAA432A3A5EEC37338EDA7F07E5D1F5E79A4336CA1DEFB0`.
- Inverse-rotation and compensated spacing decode: original adjacent gaps
  `1.791184-2.048935 mm` (median `1.915371 mm`); corrected file
  `1.899351-1.931536 mm` overall, with off-centre sampled columns varying by
  at most `0.000216 mm`.
- All four corrected layers decode to the same equidistant lattice. The
  per-channel fitted base pitch was cyan `1.915506`, magenta `1.915488`,
  yellow `1.915457`, and black `1.915490 mm`; maximum residual to an integer
  row plane was `0.001125 mm` or less. Allowing for tone-masked rows merely
  produces integer multiples of that pitch.
- `python tools/check_gcode_motion.py ... --strict` and
  `python tools/check_macros.py ...` pass on all four corrected files.
- Method, per-column measurements, and the correction boundary are recorded in
  `docs/report/lab-notes/2026-10-29-ben2-yellow-row-spacing-classification.md`.

## Struggles and rejected approaches

The shared phase makes crest/trough alignment look regular, but it cannot make
rows equidistant while allowing each row's amplitude to follow tone. Changing
bed compensation or adding another mesh cannot correct unequal source
geometry. Those remain appropriate only for residual machine-position error.

## Risks and follow-up

The corrected four-file set has not yet been verified on paper. This analysis
does not rule out residual mechanical following error, lost steps, or
pen-drag effects; it establishes that the original file requested unequal row
gaps before the machine moved. Use **Wave screen - equidistant rows** when
constant pitch is the hard requirement.

## Files

- `software/generator_tabs/cmyk_tab.py`: explicit label, tooltip, and manifest
  phase-mode metadata.
- `software/tests/test_cmyk_tab.py`: variable-depth spacing and manifest
  regressions.
- `software/README.md`: current Wave-screen spacing semantics.
- `software/converter_core/cmyk.py`: current style documentation.
- `samples/gcode/Ben2/*-equidistant.gcode`: complete four-ink Ben2 program set
  with the original frame and exact-pitch rows.
- `samples/gcode/Ben2/PXL_20201128_211515508-cmyk-equidistant-set.json`: shared
  recipe, hashes, preflight results, and equidistance audit.
- `docs/report/lab-notes/2026-10-29-ben2-yellow-row-spacing-classification.md`:
  decoded spacing evidence and physical-test boundary.
