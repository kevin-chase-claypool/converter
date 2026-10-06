---
id: WSW-20261006-019
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs
tags:
  - user-interface
  - generators
  - scale
related:
  - WSW-20261006-015
  - WSW-20261006-017
---

# Raise Artwork scale to 1000 percent

## Summary

Every generator tab's **Artwork scale** control now ranges from 10% to 1000%,
up from the previous 200% ceiling.

## Reason

The owner asked for the 200% limit to be raised to 1000%.

## Implementation

- The nine generator tabs (`flow_field_tab`, `line_draw_tab`, `three_d_tab`,
  `harmonograph_tab`, `snowflake_tab`, `truchet_tab`, `text_tab`,
  `substitution_tab`, `postcard_tab`) create their scale spin box with a
  10-1000 range; the 5% step and 100% default are unchanged.
- `software/tests/test_generator_tabs.py` asserts every generator page's
  scale control has a 1000 maximum.

## Verification

- `python -m unittest discover -s software\tests -p "test_generator_tabs.py" -v`
  -> the per-tab scale test checks default 100 and maximum 1000 for all nine
  generator tabs.
- Full suite: `python -m unittest discover -s software\tests` -> 261 tests
  pass.

## Struggles and rejected approaches

None; the scale helper already accepts factors above 2.0.

## Risks and follow-up

- Generator pages preview 1:1, so very large scales push most of the drawing
  outside the page viewBox and it is clipped. That is the requested range; the
  clip warning in the preview panel reports artwork outside the reach circle.

## Files

- `software/generator_tabs/*_tab.py`: scale spin-box range.
- `software/tests/test_generator_tabs.py`: maximum-range assertion.
- `software/README.md`: control range.
