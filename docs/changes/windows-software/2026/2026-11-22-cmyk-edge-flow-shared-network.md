---
id: WSW-20261122-004
date: 2026-11-22
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/converter_core/structure_tensor.py
  - software/generator_tabs/cmyk_tab.py
tags:
  - cmyk
  - edge-flow
  - streamline
  - registration
  - shared-geometry
  - portrait
related:
  - WSW-20261122-002
  - WSW-20261122-003
---

# Make edge-flow CMYK plates share one streamline network

## Summary

Edge-flow CMYK now traces one common streamline network from the union of all
four ink masks and uses the same seed for every plate. Cyan, magenta, yellow,
and black select portions of those identical paths with their own tone
thresholds, so coincident coverage overprints on one centerline instead of
forming four adjacent rainbow lines.

## Reason

The processed-RGB structure tensor restored color-only edges, but each ink
still entered the tracer with a different seed and a different occupancy map.
On the displayed `IMG_0514.JPG` portrait this produced strong color fringes
around the face and clothing: the software preview looked like a clown mask
rather than the mixed-ink behavior shown by the public r/PlotterArt reference.
Using one seed alone reduced the offset but did not align paths because each
ink stopped, started, and reserved space from a different tone mask.

## Implementation

- `prepare_image_tones()` publishes `flow_coverage`, the per-pixel maximum of
  the separated C/M/Y/K masks.
- `screen_channel(style="edge_flow")` accepts an optional `flow_coverage`.
  Placement, tracing, layer thresholds, and occupied-cell spacing use this
  common coverage rather than one ink's mask.
- `trace_structure_streamlines()` traces each complete common path, splits it
  into visible runs for the current ink, and reserves the full path so later
  inks cannot select a neighboring streamline.
- The CMYK tab uses the base Seed value, without the per-ink increment, for
  edge-flow only. Other screen styles retain their existing per-ink seeds.
- The saved manifest identifies the combined guide and network mode as
  `shared_processed_rgb_structure_tensor_union_coverage`.

## Verification

- A new regression first failed with four distinct seeds. It now proves all
  four edge-flow calls receive one seed and the same coverage array.
- A geometry regression uses two different tone masks over one common coverage
  field and proves every magenta point lies exactly on the cyan path network.
- All `111` CMYK test-module tests pass.
- Complete converter discovery passes `631` tests with one expected
  OpenGL-context skip.
- The live 1600 px preview retained facial, eye, mouth, shirt, wood, and
  background detail while changing the face from saturated rainbow fringes to
  mostly neutral mixed-ink lines with color accents. A four-pen paper print
  remains the physical validation gate.

## Struggles and rejected approaches

Changing only the seed repaired the deterministic starting grid but not the
ink-specific growth and stopping rules. Letting each ink continue tracing
through its own mask still allowed neighboring lines to be claimed by
different colors. Reserving cells from a per-ink occupancy map preserved that
registration defect, so the common coverage map is now authoritative for
geometry while plate tone remains authoritative for visible segments.

## Risks and follow-up

Shared geometry increases alignment but can split a long path into shorter
ink-specific runs at color boundaries. The paper test still must verify
centerline overlay, pen saturation, line spread, and whether the selected
pitch and three layers are useful for the physical pen set.

## Files

- `software/converter_core/cmyk.py`: union coverage field and public
  `flow_coverage` input.
- `software/converter_core/structure_tensor.py`: common-path occupancy and
  per-ink run masking.
- `software/generator_tabs/cmyk_tab.py`: shared edge-flow seed, coverage
  handoff, and manifest mode.
- `software/tests/test_cmyk_tab.py`: shared-seed and shared-geometry
  regressions.
- `software/README.md`: current overprint behavior.
- `docs/project/ENGINEERING_LOG.md`: implementation and verification event.
