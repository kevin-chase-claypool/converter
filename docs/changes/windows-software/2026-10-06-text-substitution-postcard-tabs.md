---
id: WSW-20261006-018
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
  - text
related:
  - WSW-20261006-016
  - WSW-20261006-017
  - docs/research/2026-10-06-r-plotterart-svg-generators.md
---

# Add Text, Substitution, and Postcard generator tabs

## Summary

The converter now has three more generator tabs, each with its own settings
and **Artwork scale** control: **Text** (monoline Hershey simplex lettering),
**Substitution** (2x2 colour-substitution patterns), and **Postcard**
(plottable postcard-back layouts). The tab bar is now Convert, Flow Field,
Line Draw, 3D Wireframe, Harmonograph, Snowflake, Truchet, Text, Substitution,
Postcard.

## Reason

These are the next non-duplicate features from the r/plotterart survey:
monoline text (the survey's text tools), the MIT `piebro/substitution-system`,
and the Unlicense `cadin/plotter-postcard`. Monoline text needed font data, so
the public-domain Hershey simplex `.jhf` file was vendored instead of
depending on a package.

## Implementation

- `_hershey.py`: parser and layout for the Hershey simplex font, written from
  the published format notes. `fonts/futural.jhf` is the 3.5 KB public-domain
  font data, kept in its original format with its use terms in
  `fonts/NOTICE.md`.
- `text_tab.py`: multi-line text, size, tracking, line spacing, alignment,
  page/margin/line width, artwork scale.
- `substitution_tab.py`: palette count, iterations (grid doubles each time),
  seed, and two single-pen renderings - colour boundaries or one diagonal per
  cell. Algorithm re-implemented from the MIT source.
- `postcard_tab.py`: page presets (5x7 in, A6, A5, 140 mm square), border,
  centre divider, stamp box, address guide lines, and optional caption/address
  text drawn with the Hershey font. Layout concept from the Unlicense source.
- `__init__.py` order constants keep the new tabs after Truchet.

## Verification

- `test_text_tab.py` -> 5 pass, including glyph-shape checks ('I' one stroke,
  'H' three), layout advance, determinism, and tab build.
- `test_substitution_tab.py` -> 5 pass: grid size 2^(n+1), seed determinism,
  both styles, SVG/XML, tab build.
- `test_postcard_tab.py` -> 5 pass: border/stamp/address geometry, text adds
  strokes, determinism, SVG/XML, tab build.
- Shell test asserts the ten-tab order and that every generator page has an
  Artwork scale control.
- Offscreen render of "HELLO 123" in the Hershey font confirmed the letter
  shapes before committing.
- Full suite: `python -m unittest discover -s software\tests` -> 261 tests
  pass.

## Struggles and rejected approaches

- The `.jhf` pen-up marker is the two characters `" R"`, and its `R` is shared
  with the next coordinate pair; splitting the data on spaces produced wrong
  glyphs until the parser consumed the marker as a pair.
- Converting the font to the US NTIS format is forbidden by the data's use
  terms; the original `.jhf` stays in place and is parsed at runtime.
- Using a package or an unlicensed r/plotterart font was rejected in favour of
  the public-domain data with explicit acknowledgements.

## Risks and follow-up

- Text wider than the page is clipped at the viewBox edge; reduce text size or
  tracking, or raise the page width.
- Substitution iterations are capped at 7 (a 256 x 256 grid); larger grids
  produce tens of thousands of paths.

## Files

- `software/generator_tabs/_hershey.py`, `fonts/futural.jhf`,
  `fonts/NOTICE.md`: font data and layout.
- `software/generator_tabs/text_tab.py`, `substitution_tab.py`,
  `postcard_tab.py`: tabs.
- `software/generator_tabs/substitution_NOTICE.md`,
  `postcard_NOTICE.md`: attribution.
- `software/tests/test_text_tab.py`, `test_substitution_tab.py`,
  `test_postcard_tab.py`: coverage.
- `software/README.md`: tab list and font terms pointer.
