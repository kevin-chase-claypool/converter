---
id: WSW-20261023-008
date: 2026-10-23
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_cmyk_tab.py
  - software/tests/test_generator_tabs.py
tags:
  - cmyk
  - planning
  - cancel
  - ui
  - background-worker
related:
  - WSW-20261023-007
---

# Route the shared Cancel button to CMYK background planning

## Summary

The shared preview **Cancel** button now changes to **Cancel planning** and
remains enabled while a CMYK tab is calculating its four per-ink G-code
programs. Clicking it cancels that active background planner.

## Reason

After the fast preview completed, the preview worker was finished and its
Cancel button became disabled. The CMYK tab immediately started a second
background worker for the four exact programs, leaving the operator watching
status messages such as `Planning Cyan...` with no visible way to stop it.
The CMYK-local cancel button existed, but could be outside the visible portion
of the scrolling controls.

## Implementation

- CMYK planning start/finish now publishes its state through
  `generator_planning_changed`.
- The shared Cancel button retargets to the active generator worker, changes
  its label to **Cancel planning**, and disables itself while cancellation is
  pending.
- Cancellation calls the tab's existing `cancel_analysis` path, preserving the
  worker cancellation event, status update, and last-results behavior.
- When planning finishes or is cancelled, the shared button returns to its
  normal disabled **Cancel** state.
- The CMYK-local Cancel planning button remains available for discoverability.

## Verification

- The implementation was developed against a failing regression that
  reproduced the disabled shared button during an active background planner.
- The regression confirms that clicking the shared button invokes the active
  tab's `cancel_analysis`, and that completion restores the normal button label
  and disabled state.
- A second CMYK-tab regression confirms planning start/finish controls both the
  local cancel/save buttons and the host-facing planning state.
- The full converter suite passes `490` tests with one OpenGL-context skip.

## Struggles and rejected approaches

- Keeping only the CMYK-local Cancel button was rejected because it does not
  solve the reported interaction: the prominent shared control still appears
  disabled while work is running.
- Treating the completed preview thread as cancellable was rejected because
  its worker no longer exists; cancellation must target the tab's independent
  background planner.
- Automatically scrolling the sidebar to the local button was rejected as a
  fragile UI workaround.

## Risks and follow-up

- Only tabs that expose `analysis_running` and `cancel_analysis` participate in
  the shared planning control. Tabs that add background analysis later should
  publish the same state.
- Cancellation remains cooperative: the worker checks its cancellation event
  between ink programs, so already-running per-ink planning may take a short
  time to finish.

## Files

- `software/generator_tabs/cmyk_tab.py`: planning-state publication and host
  synchronization.
- `software/qt_svg_to_gcode.pyw`: shared Cancel routing and label/state
  management.
- `software/tests/test_cmyk_tab.py` and
  `software/tests/test_generator_tabs.py`: regression coverage.
- `software/README.md`: operator-facing cancel behavior.
