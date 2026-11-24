---
id: WSW-20261123-019
date: 2026-11-23
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/converter_core/cmyk.py
  - software/tests/test_cmyk_tab.py
  - software/README.md
  - docs/proposals/flow-field-cmyk.md
  - docs/project/ROADMAP.md
tags:
  - cmyk
  - edge-flow
  - per-ink
  - structure-tensor
  - four-file-output
  - photo-reproduction
  - pen-down
related:
  - WSW-20261123-018
  - WSW-20261122-002
  - WSW-20261123-011
---

# Restore independent per-ink Edge-flow networks

## Summary

The production **Edge-flow streamlines (structure tensor)** style again screens
each CMYK pen through its own independently seeded and angled structure-tensor
network. It saves the same four separate G-code programs. The prior
co-located model remains available as **Shared Edge-flow (experimental
co-located CMYK)**.

## Reason

The reference print supplied by the owner uses the workflow described in the
`r/PlotterArt` post: image gradients form a structure tensor, the tensor is
blurred, evenly spaced streamlines follow that direction field, darker areas
gain layers, and weak-structure regions use a fixed fallback angle. The four
inked plates must therefore be independently screened and then printed over
one another.

`c3f07ed` replaced that workflow with one shared network for all inks.
`WSW-20261123-018` corrected the resulting correlated black overprint, but it
kept the shared network as the only CMYK Edge-flow path. The four save files
were still generated, but they no longer exercised independent streamline
geometry.

## Implementation

- The default `edge_flow` style calls `screen_channel()` once per ink with the
  seed offset by channel and the matching fallback angle from
  `SCREEN_ANGLES_DEG`.
- C, M, Y, and K each receive their own structure-tensor trace, path-local tone
  gating, dark-tone layers, and pen-down bridge/chain behavior.
- Black keyline boosting applies only to the Black network. C/M/Y edge quieting
  applies only to the corresponding color networks.
- `edge_flow_shared` retains the co-located experiment and uses
  `screen_cmyk_edge_flow()` only when explicitly selected.
- The calibration sheet maps the shared style back to one representative
  per-ink Edge-flow coupon rather than claiming to calibrate co-located screen
  behavior that has not been validated on paper.
- The set manifest records `edge_flow_path_network: per_ink` for the restored
  production mode and `shared_all_inks` for the experimental mode.

## Verification

- A new tab regression patches the actual layer builder and asserts exactly
  four `screen_channel()` calls with seeds `7/8/9/10`, the four fallback
  angles, one shared luminance guide, Black-only keylines, and non-Black edge
  quieting.
- The regression also asserts that the shared screen is not called for the
  default style and that four distinct layer files are produced.
- A rendered check of the live portrait recipe at `260 %` produced
  `16,364` total marks across four independent networks (`2,116 / 2,218 /
  4,749 / 7,281` for C/M/Y/K), `61.91 %` dark ink-union pixels, only `0.10 %`
  four-ink overlap, and `0.304` mean luminance on the inked union. The result
  is independently colored linework rather than the shared renderer's black
  mass.
- The shared experimental path has its own regression asserting one call to
  `screen_cmyk_edge_flow()`.
- The saved-set regression requires the manifest to identify `per_ink` paths
  and the per-ink structure-tensor guide.
- `python -m unittest software.tests.test_cmyk_tab.CmykTabTests -v` passes all
  `62` tab tests.
- Complete converter discovery passes `666` tests with one expected
  OpenGL-context skip.
- `python tools\docs_index.py --write` rebuilt five indexes, and
  `python tools\docs_index.py --check` passes for all `530` change notes.

## Struggles and rejected approaches

Fully reverting `c3f07ed` would remove the shared implementation and its
regressions. Keeping both modes is safer because the shared renderer remains
useful for comparing co-located color mixtures, while the independent mode
restores the documented reference algorithm.

## Risks and follow-up

- Independent networks place colors on different paths, so registration,
  visible connector ink, and local colour mixing still require a physical
  four-pass print.
- Enabling the nearest-endpoint chain reduces penups but can draw visible
  connectors between otherwise separate streamline fragments.
- The shared experimental mode remains software-validated only.

## Files

- `software/generator_tabs/cmyk_tab.py`: distinct per-ink and shared styles,
  per-channel screening arguments, and manifest identity.
- `software/converter_core/cmyk.py`: Auto recognizes both Edge-flow styles.
- `software/tests/test_cmyk_tab.py`: four-file/per-ink regression and retained
  shared-path coverage.
- `software/README.md`: restored workflow and experimental shared-mode
  documentation.
- `docs/proposals/flow-field-cmyk.md`: current implementation description.
- `docs/project/ROADMAP.md`: current validation status.
