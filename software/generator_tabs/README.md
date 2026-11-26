# Generator tabs

The converter window shows one tool page at a time in a `QStackedWidget`. The
**All tools** dashboard lists every page as a card, grouped by category, and
the **Tools** menu selects any page (Ctrl+T opens the dashboard, Ctrl+1 is
Convert, Ctrl+2...Ctrl+0 follow menu order).
**Convert** is the default page; every `*_tab.py` module in this package is
auto-discovered and added as one tool page.

Import, Preview/Save, and the preview panel are static window chrome. Pressing
**Preview** builds the *active* tab: Convert uses the Artwork row, while a
generator tab is built by its own `build_svg()`. The result runs through the
normal converter pipeline and is drawn in the one shared preview panel;
**Save G-code** exports that same result. Switching tabs never rebuilds
anything - it only marks the visible preview as belonging to another tab.

## Tab contract

```python
TITLE = "Flow Field"

GROUP = "Line art"          # dashboard group
DESCRIPTION = "Streamlines from noise or image tone."

def create_tab(host):
    return FlowFieldTab(host)


class FlowFieldTab(GeneratorTab):
    NAME = "flow-field"

    def build_svg(self):
        ...  # build from the current controls, return the SVG path
```

`host` is the `MainWindow` and exposes:

- `host.artwork_path()` — the file currently loaded in the static **Artwork**
  row. Tabs that consume raster or SVG artwork use this and never add a second
  import path.
- `host.generator_status(text)` — write the shared status line.
- `host.log` — the bottom log widget.
- `host.settings_for_source(tab)` — the converter settings for this page
  (generator tabs are plotted 1:1, and a tab with `SELF_SCREENED = True` gets
  the Fill patterns switched off so its own tone marks are not hatched again).
- `host.motion_estimate_scale()` — the display-only controller-time scale.
- `host.analyze_program(svg_path, settings, cancel_check=None)` — build the
  exact program a Preview would (moves, G-code, stats) without touching the
  UI; safe to call from a tab's worker thread.
- `host.resolve_program_set_base(default_base="")` — optional pre-resolution of
  the one save base, so a tab can include its manifest in the transaction.
- `host.export_program_set(entries, base_path=None, default_base="",
  companion_files=None)` — one save dialog, then one
  `<base>-<label>.gcode` file per `(label, gcode)` entry. Companion files join
  the same staged transaction.

Optional multi-layer hook (CMYK):

- `preview_layers()` — return ordered `(ink, svg_path)` pairs for every
  layer. The host loads each layer separately and tags its contours
  (`converter.tag_ink`), so the shared OpenGL preview draws every ink in its
  own colour; the contour order must match the tab's combined SVG. Tools that
  do not implement this hook keep the single-colour preview.
- `preview_visible_inks()` — optional; return the ink keys the tab's preview
  checkboxes currently show. The host keeps every layer loaded and filters
  drawing live via `GLPreview.set_visible_inks`, so toggling a layer costs
  neither a re-screen nor a re-plan.
- `on_preview_finished()` — called by the host after a successful preview of
  this tab. The CMYK tab uses it to plan the four per-ink programs in the
  background, so no separate "analyze" step or button exists; Save reuses
  those programs.

An embedded application may own a file workflow when its generated document
already contains named process inks. Plotterfun Extended uses this exception:
it splits the page into four internal SVGs, calls
`host.analyze_program(...)` for each layer with one shared fitted frame, and
writes the resulting Y/M/C/K G-code as a set. The internal SVGs stay outside the
selected G-code folder.

Two CMYK pages share the same tuner implementation. **CMYK** is the original
full control surface with every tuner option visible. **CMYK Photo** is the
guided production page: it subclasses the tuner, hides its control column by
default, and owns the image and folder choices. Both use the same
`build_svg()`, preview, `analyze_program()`, and four-file export path. The
guided page's 250 mm square stays inside the 14-inch circle, and its output
order is Y/M/C/K. Its guided presentation may hide the main window's
Preview/playback/fit chrome while active; it must restore those widgets when
switching to advanced or leaving the tool. Its persistent nine-stage rail
filters the advanced inspector, persists per-stage locks in the artwork recipe,
and may open auxiliary diagnostic inspectors such as the structure-field
image. Those inspectors never replace the one shared physical print preview.

Rules:

1. Keep the tab self-contained in this package; do not edit the main window or
   another tab to make yours work.
2. Implement `build_svg()`. It returns the path of a written SVG, or raises
   `ValueError` with a user-facing message when required input is missing.
3. Do not add a competing primary print preview, a per-tab file picker, or a
   hand-off button. Auxiliary stage diagnostics may use their own inspector
   window, but the simulated paper result remains in the shared preview.
   The static Preview/Save buttons and the shared preview panel own all of
   that. A multi-layer tool (CMYK) may add a Save-set button and an
   `on_preview_finished()` hook for background work; the host owns the dialogs
   and writes the files.
4. Do not implement a second converter. Emit SVG and let the host's
   `analyze_program`/`export_program_set` produce and save programs. A
   multi-file embedded workflow may stage the host-generated programs when its
   output contract is one complete print set.
5. Keep controls proportional to the generator's real parameters, and make the
   output deterministic for a given seed so it can be reviewed and tested.
6. Ported or vendored third-party code must keep its license and attribution
   in a sibling `<name>_NOTICE.md` and in a module docstring.
7. Add tests under `software/tests/test_<name>_tab.py` following the existing
   `unittest` style.

The `GROUP` and `DESCRIPTION` class attributes feed the dashboard cards; keep
the description to one short line.
