# Lab Notes

Store raw bench evidence and physical test results here. Use
[`../LAB_NOTE_TEMPLATE.md`](../LAB_NOTE_TEMPLATE.md).

Filename format:

```text
YYYY-MM-DD-test-id-short-title.md
```

Examples:

```text
2026-06-08-e-11-main-supply-check.md
2026-06-10-m-01-x-axis-jog.md
```

Each note should link to the relevant test in
[`../../testing/TEST_PLAN.md`](../../testing/TEST_PLAN.md), affected change note,
wiring-table rows, and engineering-log event. Keep measured values and failed
attempts here; summarize conclusions in the subsystem change note. For every
`E-*` test, the note must state the physical/software configuration, exact
procedure, measurements and outcome, difficulties encountered, corrective
action, and repeat evidence supporting a pass. If any code, commands, or
configuration were used, paste the exact version in a fenced code block in the
note; a source-file reference alone is insufficient.

## Index

Newest notes appear first.

| Date | Test ID | Result | Summary |
|---|---|---|---|
| 2026-09-05 | M-01 partial | Initial pass/partial | A moved counterclockwise/clockwise at `F120`, Y moved north/south at `F60`, and X moved east/west at `F60`; supply current was approximately 0.44/0.43/0.42 A. X returned exactly after ten cycles; Y/A repeatability and heating remain open. |
| 2026-09-05 | E-03 | Passed | Installed X/Y/A TB6600 signal response passed: active-low enable, opposite DIR states, and approximately 5 V STEP pulses through the common-cathode harnesses. |
| 2026-08-19 | E-01 partial | Pass/partial | All 17HS15 coil pairs were identified by hand-turn generated voltage; Y's shielded cable continues black/green and red/white, with white spliced to motor blue. |
| 2026-08-12 | E-14B partial | Pass/partial | Local 6 V branch and S7V8F5-to-Pro-Micro power path passed continuity and bench-power checks; no motor or upstream regulator test. |
| 2026-08-10 | E-18 partial | Mixed | U1/U2/U3 and ground isolation passed after repairing missing wires; actual RP23CNC terminal behavior and magnetic-adapter work remain. |
