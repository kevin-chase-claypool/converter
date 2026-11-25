---
id: WSW-20261125-007
date: 2026-11-25
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/_plotterfun_cmyk.py
  - software/generator_tabs/_plotterfun_gcode.py
  - software/generator_tabs/_plotterfun_simple.py
  - software/generator_tabs/_plotterfun_web.py
  - software/generator_tabs/plotterfun_extended_tab.py
  - software/tests/test_plotterfun_cmyk.py
  - software/tests/test_plotterfun_gcode.py
  - software/tests/test_plotterfun_tab.py
  - software/tests/test_generator_tabs.py
  - software/README.md
tags:
  - plotterfun-extended
  - cmyk
  - gcode
  - registration
  - user-interface
  - print-workflow
  - flow-field
  - tone
  - gcr
related:
  - WSW-20261125-006
  - WSW-20261007-012
---

# Simplify Plotterfun Extended and generate registered Y/M/C/K G-code

## Summary

Plotterfun Extended now opens in a compact three-step CMYK workflow instead of
showing the complete upstream control sidebar. One action writes four
ready-to-run G-code files and a manifest into a selected folder. Every program
keeps the same fitted page and registration marks, and the filenames encode the
physical print order: Yellow, Magenta, Cyan, Black.

The full upstream application remains available behind **Advanced controls**.
Its blue **Download SVG** action is unchanged and still produces one combined
SVG. It is not the four-pass workflow.

## Reason

The embedded page exposed Source, Color, Parameters, page size, pen controls,
and export controls all in one narrow settings column. The owner reported that
the result was cluttered and that it was unclear whether **Download SVG**
separated CMYK.

It did not. The page's downloadable SVG contains all named channel groups in
one file. The owner then clarified that the useful deliverable is one G-code
program per ink, not four SVGs that must be imported manually. The workflow must
also preserve tone-dependent line pitch: Flow Field uses darker pixels to
increase streamline density, and the black channel carries the gray component
from CMYK separation.

## Implementation

- `_plotterfun_cmyk.py` splits the page SVG by its named `yellow`, `magenta`,
  `cyan`, and `black` groups. It preserves the root `width`, `height`,
  `viewBox`, style, defs, and clip paths, then normalizes the light process
  paints to black only in the internal geometry so the single-pen parser cannot
  discard cyan or yellow as near-white artwork.
- Each standalone layer receives the same four corner registration crosses.
  Those crosses make each layer's measurable bounds identical. The Plotterfun
  tab then uses its normal auto-fit in **Fit inside** mode, so all four G-code
  programs inherit one scale and page centre.
- `_plotterfun_gcode.py` sends every internal layer through the main converter's
  `analyze_program` path. This preserves the current bed compensation, pen
  settings, motion guards, and exact G-code generation used by Convert.
- Public output is `<base>-01-yellow.gcode`, `02-magenta`, `03-cyan`, and
  `04-black`, followed by `<base>-cmyk-set.json`. The manifest records source
  artwork, algorithm, per-file SHA-256 hashes, line and contour counts, missing
  channels, and the instruction to run the files in numeric order on one sheet
  without moving or re-registering the paper.
- The split SVGs are written to a temporary internal work folder and are
  referenced by the manifest as intermediates. They do not appear in the
  selected output folder. If a channel has no artwork, its G-code file is still
  emitted with the registered boundary marks and identified in the manifest.
- `_plotterfun_simple.py` owns the three-step UI, waits for generation to finish
  before capture, generates the four programs in a worker thread, remembers the
  chosen folder for the session, and asks once before replacing an existing set.
  `_plotterfun_web.py` remains the shared WebEngine host used by both
  Plotterfun tabs.
- The injected simple-page mode hides the upstream header, sidebar, and footer
  with `!important` CSS and uses the full workspace rather than leaving the
  embedded preview beside an empty GL pane. **Advanced controls** reveals the
  complete page and restores the converter preview. **Open combined SVG in
  Convert** is available only in advanced mode.
- **Use current artwork** now waits for the image preview, presses the page's
  internal **Use image** action, forces CMYK with K enabled, and starts the
  selected style without making the user find those controls.

## Verification

- Focused Plotterfun split, G-code, and UI tests pass 21 tests.
- The main-window integration test verifies Flow Field is the default, the
  fitted CMYK page disables the generic fill pass, every ink produces `M3`
  drawing commands, and all four layers choose one scale.
- Complete converter discovery passes `714` tests in `135.680 s` with one
  expected OpenGL-context skip.
- Split tests verify channel isolation, root page preservation, defs/clip-path
  preservation, four registration crosses in every file, Y/M/C/K ordering,
  manifest hashes, blank missing channels, and identical parsed geometry bounds
  across all four layers.
- Live visual review in the actual dark-themed main window passed: the simple
  card is readable, the preview uses the full workspace, and the advanced
  toggle restores the standard converter preview.
- A live default Flow Field run on the supplied colorful photograph emitted
  four nonempty files: yellow `2,089,190` bytes, magenta `682,047`, cyan
  `606,359`, and black `6,311,363`. The black/K program had `106,340` drawing
  moves versus yellow `34,222`, magenta `10,686`, and cyan `9,575`, confirming
  that Flow Field pitch and the K gray component both contribute visible tone.
- All four Flow Field programs pass
  `python tools\check_gcode_motion.py --strict` with no bare rotation rapids and
  A rates below the configured limit.

## Struggles and rejected approaches

Using the upstream blue **Download SVG** button directly was rejected because
it emits one combined document and cannot establish four independent physical
passes. The first implementation's four-SVG deliverable was also superseded
when the owner clarified that the SVGs should be internal and the output should
be directly plottable G-code.

Editing the minified production bundle was rejected. Injecting a small CSS/JS
mode from the Python host keeps the pinned third-party build intact and leaves
the complete advanced interface available.

Making each file's artwork bounds equal by changing the drawing geometry was
rejected because it would move ink. Registration crosses provide a shared
measurement frame without changing the channel geometry.

The first live implementation exposed three defects: the hard-coded light card
inherited white controls in dark mode, the embedded page was squeezed beside an
empty preview pane, and QtWebEngine did not deliver JavaScript object results.
The card now uses the application palette, simple mode hides the unused GL pane,
and the page bridge returns JSON text.

The first G-code conversion also clipped nearly all Plotterfun geometry because
its 800 x 600 viewBox was treated as millimetres and because the converter
filters near-white cyan/yellow. Internal black paint normalization and a shared
**Fit inside** transform corrected both issues without changing the visible
source artwork.

## Risks and follow-up

- The registration crosses are intentionally plotted by every pass. They make
  overlay registration visible, but the owner should confirm that the mark size
  suits the installed pen and paper.
- Four G-code files have passed software and motion preflight, but the physical
  Y/M/C/K overlay has not yet been printed and inspected.
- Flow Field can take minutes on a dense photograph; the simple status line
  reports generation and G-code progress, but no cancel action is exposed yet.
- The simple mode depends on stable selectors in the pinned Plotterfun bundle.
  A future vendor update must rerun the UI and export tests.
- Internal SVG intermediates remain in the system temporary directory for
  diagnostic traceability. They are not part of the selected output folder.

## Files

- `software/generator_tabs/_plotterfun_cmyk.py`: pure SVG split, registration,
  paint normalization, and internal SVG-set hashes.
- `software/generator_tabs/_plotterfun_gcode.py`: per-ink G-code naming,
  staging, hashes, and public manifest generation.
- `software/generator_tabs/_plotterfun_simple.py`: simple/advanced UI, page
  injection, generation wait, worker-thread G-code generation, folder
  selection, and status reporting.
- `software/generator_tabs/_plotterfun_web.py`: shared WebEngine host and
  Plotterfun-specific auto-fit settings.
- `software/generator_tabs/plotterfun_extended_tab.py`: enables the simple
  workflow for Plotterfun Extended.
- `software/tests/test_plotterfun_cmyk.py`: page-registration and export tests.
- `software/tests/test_plotterfun_gcode.py`: printed-order G-code set tests.
- `software/tests/test_generator_tabs.py`: main-window fitted-page integration
  test.
- `software/tests/test_plotterfun_tab.py`: UI and fallback workflow tests.
- `software/README.md`: current operator workflow and output contract.
