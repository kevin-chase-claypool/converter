# Plotterfun Extended tab - third-party notice

The Plotterfun Extended tab vendors the production build of
**msurguy/plotterfun-extended** at commit
`00bf56dd872db8797486e021c26345929463e985`.

Upstream: https://github.com/msurguy/plotterfun-extended

License: MIT, reproduced in `software/plotterfun_extended_vendor/LICENSE`.
The project is an extended React/Vite implementation of the original
**mitxela/plotterfun**, also MIT licensed.

The vendored build differs from the upstream production output only in:

- Vite `base` was changed from `/labs/plotterfun-extended/` to `./`.
- `crossorigin` attributes were removed from the generated index so it can be
  served locally without external origin assumptions.
- The optional `@huggingface/transformers` depth-model package was removed from
  this local build. Its 27 MB ONNX runtime was unnecessary for plotting and
  triggered GitHub push protection on a false-positive Mistral API key in a
  generated error-message URL. The **Depth Map** control now uses a local,
  deterministic luminance-depth proxy instead.

The converter serves this static bundle from a loopback-only local HTTP server
because Chromium blocks the upstream ES-module workers under a `file://` URL.
The wrapper's **Export SVG to plot** button serialises the page's own `<svg>`
element and adopts it as the current converter artwork.

No algorithmic worker is modified. The React page differs only in using the
local depth proxy and describing that limitation in its control. Face-boundary
landmark assets remain opt-in and may require network access on first use;
every other algorithm runs locally.
