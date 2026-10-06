# Generator tabs

The converter window is a `QTabWidget`. The first tab, **Convert**, is the
imported-artwork workspace; every `*_tab.py` module in this package is
auto-discovered and added as one tab per generator.

Import, Preview/Save, and the preview panel are static window chrome. Pressing
**Preview** builds the *active* tab: Convert uses the Artwork row, while a
generator tab is built by its own `build_svg()`. The result runs through the
normal converter pipeline and is drawn in the one shared preview panel;
**Save G-code** exports that same result. Switching tabs never rebuilds
anything - it only marks the visible preview as belonging to another tab.

## Tab contract

```python
TITLE = "Flow Field"

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

Rules:

1. Keep the tab self-contained in this package; do not edit the main window or
   another tab to make yours work.
2. Implement `build_svg()`. It returns the path of a written SVG, or raises
   `ValueError` with a user-facing message when required input is missing.
3. Do not add a per-tab preview, a per-tab file picker, or a hand-off button.
   The static Preview/Save buttons and the shared preview panel own all of
   that.
4. Never write G-code directly; emit SVG only.
5. Keep controls proportional to the generator's real parameters, and make the
   output deterministic for a given seed so it can be reviewed and tested.
6. Ported or vendored third-party code must keep its license and attribution
   in a sibling `<name>_NOTICE.md` and in a module docstring.
7. Add tests under `software/tests/test_<name>_tab.py` following the existing
   `unittest` style.
