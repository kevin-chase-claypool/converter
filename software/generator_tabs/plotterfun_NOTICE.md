# Plotterfun tab - third-party notice

The Plotterfun tab vendors the complete static site of
**mitxela/plotterfun** (https://github.com/mitxela/plotterfun), licensed under
the MIT License. The assets live unmodified in
`software/plotterfun_vendor/` (28 files: `main.htm`, `helpers.js`, the 22
algorithm scripts, `range.css`, `loading.gif`, and the upstream `LICENSE`).

The page is embedded with QtWebEngine. Interaction happens inside the
upstream app; the **Export SVG to plot** button only serialises the page's own
`<svg>` element with `XMLSerializer` and hands it to the Convert pipeline.
No upstream code was modified or ported.
