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
- `host.export_program_set(entries, base_path=None, default_base="")` — one
  save dialog, then one `<base>-<label>.gcode` file per `(label, gcode)`
  entry.

Optional multi-layer hook (CMYK):

- `preview_layers()` — return ordered `(ink, svg_path)` pairs for the layers
  currently shown. The host loads each layer separately and tags its contours
  (`converter.tag_ink`), so the shared OpenGL preview draws every ink in its
  own colour; the contour order must match the tab's combined SVG. Tools that
  do not implement this hook keep the single-colour preview.
- `on_preview_finished()` — called by the host after a successful preview of
  this tab. The CMYK tab uses it to plan the four per-ink programs in the
  background, so no separate "analyze" step or button exists; Save reuses
  those programs.

Rules:

1. Keep the tab self-contained in this package; do not edit the main window or
   another tab to make yours work.
2. Implement `build_svg()`. It returns the path of a written SVG, or raises
   `ValueError` with a user-facing message when required input is missing.
3. Do not add a per-tab preview, a per-tab file picker, or a hand-off button.
   The static Preview/Save buttons and the shared preview panel own all of
   that. A multi-layer tool (CMYK) may add a Save-set button and an
   `on_preview_finished()` hook for background work; the host owns the dialogs
   and writes the files.
4. Never write G-code directly; emit SVG and let the host's
   `analyze_program`/`export_program_set` produce and save programs.
5. Keep controls proportional to the generator's real parameters, and make the
   output deterministic for a given seed so it can be reviewed and tested.
6. Ported or vendored third-party code must keep its license and attribution
   in a sibling `<name>_NOTICE.md` and in a module docstring.
7. Add tests under `software/tests/test_<name>_tab.py` following the existing
   `unittest` style.

The `GROUP` and `DESCRIPTION` class attributes feed the dashboard cards; keep
the description to one short line.
