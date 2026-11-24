---
id: WSW-20261123-017
date: 2026-11-23
category: windows-software
affected_categories:
  - windows-software
status: superseded
components:
  - software/converter_core/structure_tensor.py
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
  - software/README.md
  - docs/proposals/flow-field-cmyk.md
  - docs/project/ROADMAP.md
tags:
  - cmyk
  - edge-flow
  - photo-reproduction
  - color-management
  - shared-path
  - registration
related:
  - WSW-20261123-018
  - WSW-20261123-016
  - WSW-20261123-015
  - WSW-20261123-005
---

# Share Edge-flow path geometry across CMYK inks

Superseded by `WSW-20261123-018`, which keeps the shared geometry but replaces
the correlated tone gate and re-enables local adjacent chaining.

## Summary

Edge-flow now traces one streamline network and applies cyan, magenta, yellow,
and black coverage along that same geometry. Local colour mixtures therefore
overprint on co-located paths instead of appearing as four independently
seeded coloured tracks.

## Reason

The process-ink model and Auto could choose a numerically accurate CMYK mix,
but the actual Edge-flow screen sent each ink through a different path network.
Colours that should overlap locally were frequently drawn beside one another,
producing the rainbow/speckle separation visible in the operator's portrait
preview. Average colour calculations could not correct a spatial geometry
error.

## Implementation

- `trace_shared_structure_streamlines()` builds one structure-tensor path
  network from the maximum channel coverage.
- Every process ink is sampled at the same path coordinates and arc-length
  phase. Per-channel tone determines which segments receive that ink; Black
  keyline boosting and C/M/Y edge quieting operate on the same common paths.
- `screen_cmyk_edge_flow()` returns the four gated layers together and applies
  overdraw symmetrically.
- The CMYK tab calls the shared screen once for Edge-flow instead of calling
  `screen_channel()` four times.
- The separate nearest-endpoint **Keep pen down** chain is not applied to
  Edge-flow because cross-path connectors defeat co-located colour. Short
  tone-off gaps still bridge along the common streamline itself.
- The saved set manifest records `edge_flow_path_network: shared_all_inks` and
  the actual chain state.

## Verification

- The focused Edge-flow suite passes `20` tests.
- The complete CMYK tab suite passes `138` tests.
- Complete converter discovery passes `663` tests with one expected
  OpenGL-context skip.
- A synthetic two-network regression now verifies more than `90 %` shared
  point overlap and that a partial channel is a geometric subset of the full
  channel.
- On the current portrait at a reduced validation resolution, channel point
  overlap against the smaller plate ranges from `54 %` to `97 %`; the former
  independent networks had no common geometric construction.
- A software process-colour render confirms that the shared paths form local
  CMYK mixtures rather than independent colour tracks. Physical print
  registration remains a separate check.

## Struggles and rejected approaches

The earlier independent-network design was chosen to imitate separate
per-ink screen directions in a reference print. That reference look is
incompatible with local photographic colour reproduction when the plotter has
four real pens: colours cannot mix where their paths do not meet.

Keeping the cross-path pen-down chain was also rejected for Edge-flow. Its
shortest-endpoint connectors join unrelated coloured paths and recreate the
same visual breakup.

## Risks and follow-up

Shared paths increase local four-ink overlap and may increase ink load and
drying time. Per-channel edge detail can also be less independent than before.
A physical four-pass portrait must verify density, bleed, registration, and
whether the common fallback direction produces visible banding. The other
screen styles and their per-channel fallback angles are unchanged.

## Files

- `software/converter_core/structure_tensor.py`: shared path tracer and
  per-channel gating.
- `software/converter_core/cmyk.py`: shared CMYK Edge-flow entry point.
- `software/generator_tabs/cmyk_tab.py`: one-network integration, chain
  behavior, and manifest metadata.
- `software/tests/test_cmyk_tab.py`: shared geometry and tab regressions.
- `software/README.md`, `docs/proposals/flow-field-cmyk.md`, and
  `docs/project/ROADMAP.md`: current reproduction behavior and tradeoffs.
