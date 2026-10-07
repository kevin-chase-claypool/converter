---
id: WSW-20261007-004
date: 2026-10-07
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/qt_svg_to_gcode.pyw
tags:
  - cmyk
  - workflow
  - preview
  - cost-analysis
  - x-theta
  - y-theta
related:
  - WSW-20261007-001
  - WSW-20261007-002
  - WSW-20261007-003
---

# Plan the four CMYK programs automatically; drop the Analyze button

## Summary

The CMYK page no longer has an **Analyze cost (4 files)** button. Reviewing the
four x_theta/y_theta splits is not a separate task: it is the same planning
pass that decides each segment's strategy inside the normal converter. A
successful **Preview** now starts that per-ink planning in the background on
its own, the tab reports each file's split and time when it finishes, and
**Save 4 G-code files** reuses those programs (planning first only when the
settings changed). The Save button and a Cancel control remain; the tab
message explains that planning is automatic.

## Reason

Project-owner feedback: "the cost analysis is something that is being
performed to decide which to use - xtheta or ytheta. nothing more. it doesnt
need a button because its a background process of the preview/saving the
gcode to its 4 files." The previous UI made an internal planner decision look
like a manual step.

## Implementation

- `software/generator_tabs/cmyk_tab.py`:
  - Removed the Analyze button and the monospace result table; the group now
    holds **Save 4 G-code files...**, **Cancel planning**, and a hint line.
  - `format_cost_summary(results)` replaces the table with one compact status
    line (`Cost: C x115/y199 3m20s, ...`); the per-ink log lines keep the
    marks, x_theta/y_theta counts, coordinated draw length and estimate.
  - `on_preview_finished()` is the new hook: after the shared preview
    succeeds it calls `start_analysis()` with no user action. Save reuses the
    cached programs when the control key is unchanged, otherwise it plans and
    then writes (`_pending_save`).
  - `shutdown_background()` cancels and joins the planner on window close.
- `software/qt_svg_to_gcode.pyw`:
  - `preview_succeeded` tracks whether the last preview completed;
    `preview_thread_finished` calls an optional tab `on_preview_finished()`
    hook only after a successful preview (never after cancel/failure).
  - `closeEvent` asks the current tab to stop background work before closing.
  - The busy message when Preview is pressed during planning now describes the
    four per-ink programs instead of an "analysis".
- No change to G-code: the per-ink planning uses the same `analyze_program`
  pipeline and r-theta solver as before; only the UI trigger moved.

## Verification

- 347 tests pass (1 skipped: the shader-compile test skips on the headless
  `offscreen` platform). New/updated coverage: the tab has no analyze button;
  `on_preview_finished()` starts planning; the host hook runs only after a
  successful preview; the one-line cost summary carries both strategy counts.
- Off-screen full-window dry run: pressing Preview for the CMYK tab finished
  the shared preview, automatically started the background planner, produced
  all four per-ink plans (`c, m, y, k`) with the summary line
  `Cost: C x115/y199 3m20s, ...`, then `export_program_set` wrote
  `art-cmyk-cyan/magenta/yellow/black.gcode`.
- `tools\docs_index.py --write` / `--check` pass.

## Struggles and rejected approaches

- Starting the per-ink planning from `build_svg()` was rejected: it runs on
  the GUI thread just before the shared preview and both passes share the raw
  geometry cache. The host hook runs it after the preview thread is finished,
  which is the safe point.
- Keeping the result table was rejected as well; the split is decision
  evidence, so it belongs in the status line and the log.

## Risks and follow-up

- Preview now also pays for the four per-ink plans; they run on a worker
  thread and can be cancelled, and Save would need the same work anyway.
- If the four-ink planning is cancelled or fails, Save re-runs it and only
  writes after it completes.

## Files

- `software/generator_tabs/cmyk_tab.py`: automatic background planning.
- `software/qt_svg_to_gcode.pyw`: preview-success hook, close handling.
- `software/generator_tabs/README.md`: hook and rule documentation.
- `software/tests/test_cmyk_tab.py`, `software/tests/test_generator_tabs.py`:
  coverage.
- `software/README.md`: workflow text.
