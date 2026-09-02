# System Data-Flow Record

This is the change-control record for the visual
[`../system_data_flow.html`](../system_data_flow.html). Use the visual as the
macro view and this document as its audit checklist.

## Record status

| Field | Current record |
|---|---|
| Scope | Host converter, ioSender, RP23CNC/grblHAL, X/Y/A motion, toolhead, P100, faults, and commissioning data |
| Visual revision | 2 — mobile-safe, adjacent-step arrows |
| Last reviewed | 2026-09-02 |
| Evidence status | Current design record; it does not claim unverified wiring or bench behavior passed |
| Change note | [`RPSW-20260902-001`](../changes/rp23cnc-software/2026/2026-09-02-current-system-data-flow.md) |

## Baseline invariants

Review these statements whenever a new observation, test result, wiring change,
or firmware change appears. A mismatch is an inconsistency to record, not a
reason to silently redraw the chart.

| ID | Expected data path | Inconsistency to flag | Authority |
|---|---|---|---|
| DF-01 | SVG → converter → saved G-code → ioSender → grblHAL | Converter streams directly to the toolhead or bypasses ioSender/grblHAL during normal operation | [`../integration/INTERFACES.md`](../integration/INTERFACES.md) |
| DF-02 | grblHAL interprets M3/M5; the toolhead receives the resulting isolated pin state | M3/M5 G-code text is forwarded to the toolhead, or the state/polarity differs from the documented contract | [`../integration/INTERFACES.md`](../integration/INTERFACES.md), [`../../firmware/pen_pressure/README.md`](../../firmware/pen_pressure/README.md) |
| DF-03 | STEP/DIR/enable flows only from RP23CNC to the three driver stages | Toolhead sensing/control is placed in the motion timing path | [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md) |
| DF-04 | HX711 force samples close the loop only within the toolhead RP2350 | Host or grblHAL participates in the real-time force loop | [`../../firmware/pen_pressure/README.md`](../../firmware/pen_pressure/README.md) |
| DF-05 | P100 captures magnetic edges and computes the centroid/A index | One GP27 edge is treated as the bed center, or the converter applies the TMAG-to-pen correction | [`../../firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`](../../firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md) |
| DF-06 | GP27/U3 remains at LIMA; PRB is a test-gated candidate | The return is reterminated to PRB before F-08 evidence or is represented as installed without that evidence | [`../integration/INTERFACES.md`](../integration/INTERFACES.md) |
| DF-07 | A motion/controller or toolhead fault reaches a safe state and the operator before retry | Automatic retry, no observable alarm, or no safe tool state | [`../integration/INTERFACES.md`](../integration/INTERFACES.md), [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md) |
| DF-08 | Persistent force profile changes only through explicit accepted service calibration | Normal boot or M3/M5 cycle overwrites the profile | [`../../firmware/pen_pressure/README.md`](../../firmware/pen_pressure/README.md) |

## Review and discrepancy procedure

1. Compare observed behavior, wiring, or code to the applicable baseline ID.
2. If it differs, add a dated engineering-log entry with the baseline ID,
   observed path, evidence, impact, and disposition: **confirmed change**,
   **documentation defect**, or **unresolved**.
3. For a confirmed design change, update the authoritative interface, wiring,
   firmware, or software document first. Update the visual and this record in
   the same commit, then add a categorized change note.
4. For a documentation defect, correct the visual/record and retain the prior
   description and reason in the engineering log.
5. For an unresolved discrepancy, leave the current diagram unchanged, mark the
   contested path in the relevant current-state document as TBD/candidate, and
   link the required test or decision.

## Revision history

| Date | Revision | Change | Evidence |
|---|---:|---|---|
| 2026-09-02 | 2 | Replaced crossing SVG connectors with responsive adjacent-step flows after mobile review. Added this control record and eight baseline invariants. | `RPSW-20260902-001`; engineering log entries `elog-20260902080550` and `elog-20260902081743` |
