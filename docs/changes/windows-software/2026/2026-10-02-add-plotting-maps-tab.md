---
id: WSW-20261002-001
date: 2026-10-02
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_kaleidoscope.pyw
  - software/plotting_maps
  - software/tests/test_maps_tab.py
tags:
  - kaleidoscope
  - maps
  - openstreetmap
  - tab
  - webengine
  - vendored
---

# Add an independent Maps tab to the kaleidoscope app

## Summary

The kaleidoscope window now has two tabs: the existing **Kaleidoscope** tab and
a **Maps** tab that embeds a local copy of `piebro/plotting-maps`, which turns
an OpenStreetMap export into a pen-plotter SVG. The map tool is a separate
plotting function, not a kaleidoscope mode: it saves an ordinary SVG and does
not touch the kaleidoscope source, design, settings or G-code.

## Reason

The operator wants to plot OpenStreetMap extracts and asked for the map tool
inside the app. It belongs in its own tab because it shares nothing with the
kaleidoscope pipeline: different input (`.osm` not artwork), different controls
and different output. Folding it into the design column would have duplicated
the sidebar conventions and implied a relationship that does not exist.

## Implementation

- `software/plotting_maps/` vendors upstream commit `b5a510d` (`index.html`,
  `LICENSE`, `d3 7.9.0`, `proj4js 2.9.2`). Three deliberate local changes make
  it offline and private: the `d3`/`proj4` script tags point at `vendor/`, the
  Plausible analytics tag and its call sites are removed, and the startup fetch
  of the 5.9 MB demo `map.osm` is dropped so the page starts empty.
  `plotting_maps/README.md` records the commit, file hashes, modifications,
  licences and the update procedure.
- `qt_kaleidoscope.pyw` wraps the existing central widget in a `QTabWidget`.
  `PlottingMapsTab` creates its `QWebEngineView` lazily on first `showEvent`,
  so nothing web-engine shaped is built until the tab is opened and the app
  still runs on a PySide6 install without WebEngine (the tab reports the
  missing module instead).
- `MapsPage` sends off-site links (the upstream "How to Use" link) to the
  desktop browser so the tab cannot navigate away from the tool.
- `Download Map` is intercepted through
  `QWebEngineProfile.downloadRequested`: the operator gets a normal save
  dialog, the file is written with the chosen name, and the tab confirms the
  saved path. `shutdown()` releases the profile hook when the window closes.

No converter-core behavior changed.

## Verification

- `node --check` on the page's inline script: passed.
- `python -m unittest discover -s software\tests`: 170 tests pass, including
  three new `test_maps_tab.py` cases that pin the tab structure, the lazy view
  and the offline page (no CDN, no analytics domain).
- Offscreen smoke run of the real window: the tab creates the view on switch,
  the page loads (`Plotting OSM Maps`), a synthetic four-node OSM way renders
  one `<path>`, and `downloadSVG()` round-trips through the save handler to a
  file that parses as SVG with the requested `300mm` width.
- Not yet exercised: a real Overpass/`osm.org` export and a plotted sheet.

## Struggles and rejected approaches

- The live site was rejected as the embedded page: the tab would die without
  a network connection and it would load the author's analytics into the app.
- A local HTTP server was rejected in favour of `file://`. The only feature
  that needs an origin is the upstream demo fetch, which is not vendored; the
  smoke run shows the load and the Blob download both work from `file://`, and
  it avoids a listener and a possible Windows Firewall prompt.
- Vendoring upstream's `map.osm` (5.9 MB, ODbL) was rejected to keep the repo
  lean; the page therefore opens empty instead of with a demo map.

## Risks and follow-up

- Qt WebEngine pulls a Chromium runtime and a helper process into the app. The
  lazy tab keeps that cost off startup, and the test suite runs without it.
- The vendored page is pinned; upstream fixes do not arrive automatically.
  `plotting_maps/README.md` has the three-step update recipe and
  `test_maps_tab.py` fails if a CDN or analytics domain reappears.
- `processOSMData` requires a `<bounds>` element, which `osm.org` and Overpass
  exports include; a hand-edited `.osm` without bounds fails in the page with
  an error dialog only in the browser console. This is upstream behavior.

## Files

- `software/qt_kaleidoscope.pyw`: tab widget, `PlottingMapsTab`, download handling.
- `software/plotting_maps/`: vendored page, dependencies, licences, provenance.
- `software/tests/test_maps_tab.py`: offline-page and tab-structure tests.
- `software/README.md`: Maps tab usage and the WebEngine requirement.
