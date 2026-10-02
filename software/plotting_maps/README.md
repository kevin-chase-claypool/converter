# Plotting Maps (vendored)

Local, offline copy of [piebro/plotting-maps](https://github.com/piebro/plotting-maps)
by Piet Brömmel: an OpenStreetMap export to pen-plotter SVG tool. It is the
**Maps** tab of `qt_kaleidoscope.pyw` and is deliberately independent of the
kaleidoscope pipeline - it saves an ordinary SVG and never touches the
kaleidoscope settings, preview or G-code.

## Pinned upstream

- Repository: <https://github.com/piebro/plotting-maps>
- Commit: `b5a510ddc9cec7f5f86dc62bcebab20dfd3c4322` (2026-08-05)
- Vendored: 2026-10-02

SHA-256 of the files as retrieved, before the local modifications below:

| File | SHA-256 |
|---|---|
| `index.html` (upstream) | `76C91F5191777FD0C6DC0378404F21ED7AEAEAA12BAF0E45AB166CE43C7457B8` |
| `LICENSE` | `A7B7BA5F99D4607033837B92D62163B9546BBCCFE14C6BE4C530452CA04090F2` |
| `vendor/d3.v7.min.js` | `F2094BBF6141B359722C4FE454EB6C4B0F0E42CC10CC7AF921FC158FCEB86539` |
| `vendor/proj4.js` | `A7AAB96ABFE35C3B1606FCC913F4FDD93647DD0EA3BFD9EACCD397670E533433` |

Only `index.html` and the upstream `LICENSE` were copied; the README images and
the 5.9 MB demo `map.osm` are not vendored.

## Local modifications to `index.html`

1. The `proj4js` and `d3` script tags point at `vendor/` instead of their CDNs,
   so the tool runs with no network access.
2. The Plausible analytics script tag and its three call sites were removed.
   Nothing from this tab leaves the machine.
3. `window.onload` no longer fetches the upstream `map.osm` demo, which is not
   vendored; the page starts empty and waits for **Upload OSM Export**.

Nothing else in the page or its rendering was changed.

## Vendored dependencies

| File | Version | Licence |
|---|---|---|
| `vendor/d3.v7.min.js` | d3 7.9.0 | ISC - `vendor/d3.LICENSE` |
| `vendor/proj4.js` | proj4js 2.9.2 | MIT - `vendor/proj4js.LICENSE.md` |

## Updating

1. Re-download `index.html` and `LICENSE` from the new upstream commit.
2. Re-apply the three modifications above.
3. Refresh the hashes in this file and re-run `software/tests/test_maps_tab.py`,
   which fails if the page reaches for a CDN or the analytics domain.

Map data itself is not part of this repository. OpenStreetMap data is
available under the ODbL; the tool only consumes exports the operator
downloads.
