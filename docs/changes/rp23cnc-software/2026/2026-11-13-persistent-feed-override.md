---
id: RPSW-20261113-006
date: 2026-11-13
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
status: verified
components:
  - hmi/app.js
  - hmi/styles.css
  - hmi/tests/smoke.cjs
tags:
  - touchscreen
  - hmi
  - feed-override
  - transport-controls
  - user-experience
  - navigation
related:
  - RPSW-20261113-002
---

# Make feed override persistent with Start, Pause, and Stop

## Summary

The fixed bottom control deck now contains the feed-override slider, percentage,
decrease/increase controls, and 100% reset directly above Start/Resume, Pause,
and Stop. The separate Feed Override screen and Run-page link were removed.

## Reason

Owner review compared the browser HMI with the previous QML console, where feed
override and transport commands remained together. Requiring navigation to a
separate screen interrupted the primary operator workflow.

## Implementation

- Added a feed row to the always-visible transport deck with:
  - current commanded percentage;
  - a 10–200% slider;
  - −10% and +10% actions;
  - 100% reset.
- Kept Start/Resume, Pause, and Stop in the row immediately below it.
- Removed the dedicated `feed` page, its renderer, and its Run navigation item.
- Legacy `#/feed` links now normalize to `#/run`, preserving old bookmarks.
- Feed controls remain disabled outside demo mode and do not claim to report
  actual feed.
- Moved range/input handling into the transport module so it works identically
  on every screen.

## Verification

- `node hmi/tests/smoke.cjs` verifies the 16-view hierarchy, persistent feed
  controls on every view, +10/reset behavior, legacy route redirection, and all
  prior transport/settings/splash coverage.
- A native 720×1280 screenshot confirms the two-row deck fits with the fixed
  DRO and footer and leaves the screen body scrollable.
- The deployed Pi kiosk returned HTTP 200 and remains active.

## Struggles and rejected approaches

- Adding feed controls inside only the Run page was rejected because it would
  preserve the navigation interruption the owner identified.
- Floating feed controls were rejected because they could overlap content or
  compete with dialogs.
- Removing the old route outright was rejected; `#/feed` now redirects to Run.

## Risks and follow-up

- The two-row deck uses 120 CSS pixels of fixed vertical space. Future dense
  screens must keep their content independently scrollable.
- Feed override remains simulated until the sender/supervisor adapter can
  acknowledge override commands and report actual feed.

## Files

- `hmi/app.js`: persistent feed markup, state behavior, route removal/alias.
- `hmi/styles.css`: two-row transport layout and mobile sizing.
- `hmi/tests/smoke.cjs`: persistent feed and route regression coverage.
- `hmi/README.md` and `camera-inspection/touchscreen.md`: current navigation
  and operator-control contract.
