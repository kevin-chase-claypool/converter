---
id: RPSW-20261113-009
date: 2026-11-13
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
status: verified
components:
  - hmi/index.html
  - hmi/styles.css
  - hmi/app.js
  - hmi/tests/smoke.cjs
tags:
  - touchscreen
  - hmi
  - transport-controls
  - layout
  - black-theme
  - footer
---

# Enlarge the black control deck and remove the footer text

## Summary

The persistent black feed/transport deck now occupies approximately one-sixth
of the viewport height and extends to the bottom edge. The footer containing
`DEMO — no hardware control` and `Next job ready (demo)` was removed.

## Reason

Owner review found the footer text redundant and visually noisy. The machine
controls also occupied too little vertical space compared with the previous
operator console.

## Implementation

- Removed the footer element and its render/update path.
- Set the transport height to
  `clamp(150px, calc(100dvh / 6), 220px)`.
- Split that height into two flexible rows: feed override above
  Start/Resume/Pause/Stop.
- Enlarged feed controls, slider hit area, and transport buttons to use the
  available deck height without adding additional controls.
- Removed footer-specific styling and moved toast positioning above the deck.
- Retained the black deck background and green/amber/red action identities.

## Verification

- At the native 720×1280 viewport, the rendered black region measured
  **212 pixels**, or **16.56%** of the display height.
- The rendered page contains zero matches for the removed footer strings.
- A native screenshot confirms the feed and action rows remain balanced.
- `node hmi/tests/smoke.cjs` passes all 16 views, persistent feed/transport,
  settings, splash/timeout, and navigation checks.

## Struggles and rejected approaches

- Keeping a zero-height or empty footer row was rejected; the deck now extends
  directly to the screen edge.
- Hard-coding exactly 213 pixels was rejected in favor of a viewport-relative
  height with safe minimum/maximum bounds.

## Risks and follow-up

- Removing the footer also removes its always-visible job-gate sentence. The
  current gate remains available on Home, Run, and Inspect screens; future
  backend work must ensure connection and submission state remain prominent.
- Very short browser windows use the 150-pixel minimum deck height so controls
  remain usable rather than becoming unusably compressed.

## Files

- `hmi/index.html`: footer removal.
- `hmi/styles.css`: one-sixth-height black deck, larger controls, responsive
  sizing, and footer removal.
- `hmi/app.js`: removes footer rendering.
- `hmi/tests/smoke.cjs`: updates job-gate assertions to current page content.
- `hmi/README.md` and `camera-inspection/touchscreen.md`: current layout state.
