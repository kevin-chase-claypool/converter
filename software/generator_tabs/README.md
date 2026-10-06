# Generator tabs

The converter window is a `QTabWidget`. The first tab, **Convert**, is the
existing SVG/raster-to-G-code workspace. Every `*_tab.py` module in this
package is auto-discovered at startup and added as one tab per generator, so
each tool has its own workspace instead of sharing controls with Convert.

## Tab contract

```python
TITLE = "Flow Field"

def create_tab(host):
    widget = FlowFieldTab(host)
    return widget
```

`host` is the `MainWindow` and exposes:

- `host.use_svg(path, preview=False)` — load a generated SVG into the Convert
  tab (the single entry point into the existing preview/G-code pipeline).
  `preview=True` starts the normal preview immediately.
- `host.generator_status(text)` — write the bottom status line.
- `host.log` — the bottom log widget.
- `host.artwork_path()` — the file currently loaded in the static **Artwork**
  row. Tabs that consume raster or SVG artwork must use this and must not add a
  second file picker; the window has exactly one import path.

Rules:

1. Keep the tab self-contained in this package; do not edit the main window or
   another tab to make yours work.
2. Do not add an artwork file picker to a tab. Ask the user to load it with the
   static Artwork row and read `host.artwork_path()` when generating.
3. Never write G-code directly; emit SVG and hand it to `host.use_svg`.
4. Keep controls proportional to the generator's real parameters, and make the
   output deterministic for a given seed so it can be reviewed and tested.
5. Ported or vendored third-party code must keep its license and attribution
   in a sibling `<name>_NOTICE.md` and in a module docstring.
6. Add tests under `software/tests/test_<name>_tab.py` following the existing
   `unittest` style.
