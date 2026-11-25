---
id: WSW-20261125-006
date: 2026-11-25
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
  - software/generator_tabs/_plotterfun_web.py
  - software/generator_tabs/plotterfun_extended_tab.py
  - software/generator_tabs/plotterfun_tab.py
  - software/plotterfun_extended_vendor/
  - software/tests/test_plotterfun_tab.py
  - software/tests/test_generator_tabs.py
  - software/README.md
tags:
  - plotterfun
  - plotterfun-extended
  - webengine
  - cmyk
  - flow-field
  - depth
  - face-boundary
  - third-party
related:
  - WSW-20261125-005
  - WSW-20261006-002
---

# Embed Plotterfun Extended as a local converter tool

## Summary

The converter now includes a **Plotterfun Extended** tool backed by a locally
vendored build of `msurguy/plotterfun-extended` at commit
`00bf56dd872db8797486e021c26345929463e985`. It exposes all 40 upstream
algorithms, CMYK/RGB/custom channel modes, depth-aware algorithms,
face-boundary masking, and its own SVG exporter without creating a second
desktop application.

The existing Plotterfun tab now shares the same WebEngine host. Both tabs
capture their current SVG and adopt it as Convert artwork.

## Reason

The owner explicitly requested use of Plotterfun Extended. Source review found
that its Flow Field, Contours, hatching, depth, and CMYK workflows are useful
for comparison against the converter-native coherent color-flow renderer.

The upstream React/Vite page cannot be loaded directly from `file://` because
Chromium blocks its ES-module workers. Its production output also assumed the
absolute `/labs/plotterfun-extended/` base path and retained `crossorigin`
attributes unsuitable for a local static host.

The first embedded run also exposed a Qt rendering incompatibility. The
converter forces an OpenGL 2.1 top-level context, while Qt Quick initialized
its own RHI backend; `QQuickWidget` then received no QRhi, showed a blank widget,
and made export appear unresponsive.

## Implementation

- `_plotterfun_web.py` provides the shared WebEngine tab, export capture, and a
  loopback-only static server. The server binds `127.0.0.1` on an ephemeral
  port and shuts down with the tab.
- The extended page can request `/current-artwork`, a same-origin route that
  serves only the converter's currently selected image. **Use current
  artwork** injects that response into the page's hidden image input and
  verifies the browser accepted it.
- `plotterfun_extended_tab.py` selects the vendored `index.html` and registers
  the tool as **Plotterfun Extended** at tool shortcut `Ctrl+7`.
- The existing Plotterfun tab was refactored onto the shared host without
  changing its 22-algorithm page or export behaviour.
- `qt_svg_to_gcode.pyw` now sets `QSG_RHI_BACKEND=opengl` before importing
  Qt, shares OpenGL contexts before creating `QApplication`, and explicitly
  selects the OpenGL Qt Quick graphics API. This gives `QQuickWidget` and the
  main OpenGL preview a compatible RHI.
- Export serialization now guards a missing `<svg>` and returns an explicit
  warning instead of silently doing nothing.
- The build uses relative asset URLs and removes `crossorigin` attributes from
  the generated index. Runtime assets are stored under
  `software/plotterfun_extended_vendor/`.
- The optional Transformers depth-model runtime was removed from the local
  build. The page uses a deterministic luminance-depth proxy for its depth
  controls instead, avoiding a 27 MB WASM payload and a false-positive Mistral
  key detected in a generated runtime error URL.
- `npm audit --omit=dev` reports zero production vulnerabilities.
- The vendored build is MIT licensed; the repo carries its license, source
  commit, modification list, and first-use model-download limitation in
  `plotterfun_extended_NOTICE.md`.

## Verification

- A QtWebEngine offscreen load resolved the React page, all 40 algorithm
  labels, and the CMYK and tuning controls.
- A visible-converter UI run opened **Plotterfun Extended**, loaded the current
  Golden Sunset PNG through **Use current artwork**, and remained running. The
  hidden file input then contained one accepted image file.
- After the RHI fix, the visible converter rendered the full Plotterfun
  Extended interface instead of a blank black panel. A redirected stderr run
  contained none of the previous `QQuickWidget`/`QRhi` errors.
- The full converter opened the Extended tool, loaded the current artwork, and
  remained running. Export capture now reports an empty-page warning instead of
  failing silently.
- Vendor tests confirm the page bundle, worker chunks, WASM asset, MIT license,
  loopback server, current-artwork route, missing-WebEngine fallback, and
  pinned upstream commit.
- Generator discovery and layout tests include the new tool.
- Complete converter discovery passes `699` tests in `177.008 s` with the one
  expected OpenGL-context skip.

## Struggles and rejected approaches

Loading the built page directly from `file://` produced a blank DOM host in
QtWebEngine because the upstream production build uses ES-module workers.
Serving the local directory over loopback resolved it without opening a public
port or requiring a Node process at runtime.

Porting only the Flow Field worker into Python was rejected because the owner
asked to use Plotterfun Extended itself; vendoring the complete page also keeps
its color, depth, face-boundary, and 40-algorithm workflows available.

An ad-hoc teardown probe also exposed a shutdown access violation, but the
blank-page/no-op export failure was traced separately to the QRhi mismatch
above. The actual full-converter path was exercised after the fix and did not
reproduce either failure.

## Risks and follow-up

The vendored bundle adds about `4.9 MB`. QtWebEngine remains required. Depth is
the local luminance proxy, not the upstream monocular depth model. Optional
face-boundary landmarks may need a first-use network download; all other
algorithms run locally.

Plotterfun Extended still runs its selected algorithm independently for each
CMYK channel. It is an alternative/comparison workflow, not a replacement for
the converter's shared structure-tensor ink-plane renderer.

## Files

- `software/generator_tabs/_plotterfun_web.py`: shared local web host.
- `software/qt_svg_to_gcode.pyw`: compatible Qt Quick/OpenGL startup.
- `software/generator_tabs/plotterfun_tab.py`: existing Plotterfun moved onto
  the shared host.
- `software/generator_tabs/plotterfun_extended_tab.py`: new tool entry point.
- `software/generator_tabs/plotterfun_extended_NOTICE.md`: attribution and
  build provenance.
- `software/plotterfun_extended_vendor/`: pinned local production build.
- `software/tests/test_plotterfun_tab.py`: vendor, server, and fallback tests.
- `software/tests/test_generator_tabs.py`: tool discovery and grouping.
- `software/README.md`: current runtime and workflow documentation.
