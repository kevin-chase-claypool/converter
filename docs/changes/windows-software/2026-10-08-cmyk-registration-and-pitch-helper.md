---
id: WSW-20261008-009
date: 2026-10-08
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
  - software/README.md
tags:
  - cmyk
  - registration
  - workflow
  - user-interface
related:
  - WSW-20261008-008
  - WSW-20261008-002
---

# Add registration crosses and a pen-width pitch helper

## Summary

Two art-mode workflow aids:

1. **Registration corner crosses** (Page group, default off): every ink
   layer draws the same four small crosses in the page margin (inset =
   half the margin, clamped; arms up to 2.5 mm), so a four-pass plot can be
   checked for alignment while it runs. The crosses are appended after
   artwork scaling, so they stay at fixed page positions.
2. **Match pen** button beside Dot pitch: sets the pitch to
   `pen width / artwork scale` (clamped 0.1-8 mm), putting full-tone rows
   about one pen width apart - the effective-pitch rule made one click.

## Reason

Ranked improvements 3 and 4 from
`docs/research/2026-10-08-cmyk-vs-open-source.md`: pass misalignment is the
community's top failure mode and no open tool draws registration aids into
the job; DrawingBotV3's CMYK notes recommend "Rescale to Pen Width" while
our pitch/scale/pen-width relationship lived only in tooltips.

## Implementation

- `software/generator_tabs/cmyk_tab.py`: `registration_marks` checkbox and
  `_registration_crosses`; `match_pen_pitch`; the checkbox joins the layer
  cache key.
- `software/README.md`: control list.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 396
  tests (1 skipped: the pre-existing headless shader compile). New tests:
  the eight cross polylines are identical at the end of every ink
  layer and absent when the checkbox is off; Match pen yields 0.15 mm at
  200 % scale with a 0.30 mm pen.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Placing crosses inside the artwork area was rejected: margin placement
  keeps them off the image and visible while the plot runs.
- Scaling the crosses with the artwork was rejected: alignment references
  must stay at fixed page positions.

## Risks and follow-up

- The crosses verify alignment; they do not correct it (registration stays
  mechanical). Margin under ~2 mm clamps the crosses to a 0.5 mm arm.

## Files

- `software/generator_tabs/cmyk_tab.py`: checkbox, crosses, Match pen.
- `software/tests/test_cmyk_tab.py`: coverage.
- `software/README.md`: documentation.
