---
id: HW-20260908-001
date: 2026-09-08
category: hardware
affected_categories:
  - hardware
status: planned
components:
  - docs/hardware/ESTOP_TOPOLOGY.md
  - docs/hardware/WIRING_TABLE.md
tags:
  - estop
  - safety
  - rp23cnc
related:
  - HW-20260814-005
---

# Identify and diagram the RP23CNC ESTOP screw terminal

## Summary

The RP23CNC's dedicated Halt input terminal, previously recorded as TBD, is
now identified: a 2-pin `ESTOP` screw terminal (`SIG` / `GND`), the rightmost
terminal in the "Grbl Control Inputs" group on the RP23U5XBB board, after
`DOOR`, `CY/ST`, and `FD HOLD`. The current documents now include a
photo-oriented diagram: the supplied switch's upper `1`/`NC`/`2` block (NC-A)
connects as a two-wire loop across `ESTOP SIG` and `GND`; its lower NC block is
individually insulated. No wire has been landed and E-19 has not been
performed.

## Reason

`HW-20260814-005` locked the decision to use SW1 NC-A on the RP23CNC's
dedicated Halt input, but deliberately left the exact terminal pair blank
pending agreement between the manual and the installed board's silkscreen.
The owner asked to move forward on wiring the E-stop, which required closing
that TBD first.

## Implementation

No physical wiring changed. This note records the terminal identification and
the unambiguous controller-signal-only wiring instruction:

- The RP23CNC user manual's "Key Features" board diagram
  (`docs/hardware/references/RP23CNC-user-manual.pdf`, p.6, board rev
  RP23U5XBB V1.0) labels the terminal `ESTOP` with `SIG`/`GND` pins.
- A photo of the owner's installed board (rev `RP23U5XBB V1.01` per its own
  silkscreen) shows the same terminal row and labels in the same position,
  confirming the manual's diagram matches the physical unit.
- `docs/hardware/ESTOP_TOPOLOGY.md` and `docs/hardware/WIRING_TABLE.md`
  (`SAF-004`) were updated to name the terminal instead of TBD, and both still
  state the connection is planned/identified, not landed or verified.
- The diagram designates the upper contact block from the supplied rear-switch
  photo as NC-A: connect its terminal `1` and `2` to the controller's `SIG`
  and `GND` in either order. It explicitly prohibits combining terminals from
  the two NC blocks and confirms the design does not cut motor/tool power.

## Verification

- Manual page 6 board diagram inspected (rendered from
  `docs/hardware/references/RP23CNC-user-manual.pdf`).
- Owner-supplied photo of the installed board's control-input terminal row
  compared label-by-label against the manual diagram; silkscreen reads
  `RP23U5XBB V1.01`.
- No electrical test performed. E-19 (continuity check, wiring, `$14=6`,
  ioSender Halt/Reset-Unlock behavior) remains open.

## Struggles and rejected approaches

Attempted to pull the RP23CNC manual PDF through the web-fetch/browser tools
first; GitHub's PDF viewer would not render as extractable text and a direct
raw-file download required explicit download permission. Used the manual copy
already present at `docs/hardware/references/RP23CNC-user-manual.pdf` instead
(`pdftotext`/`pdftoppm`), which was faster and matches the project's existing
reference-PDF practice from `HW-20260704-002`.

## Risks and follow-up

- The terminal name is now known, but nothing is wired. E-19 must still run
  in full: continuity check, landing the two NC-A wires, setting `$14=6`
  during the live test (not before), and confirming Halt/Reset-Unlock
  behavior in ioSender.
- `ESTOP_TOPOLOGY.md`'s "Required E-19 verification" section is the
  authoritative next-step procedure.

## Files

- `docs/hardware/ESTOP_TOPOLOGY.md`: added the "Identified terminal" section
  plus a photo-oriented NC-A-to-`ESTOP SIG`/`GND` diagram and E-19 procedure.
- `docs/hardware/WIRING_TABLE.md`: updated `SAF-004`/`SAF-005` with the
  upper/lower contact-block assignments and controller-signal boundary.
- `docs/testing/TEST_PLAN.md`: made E-19's contact, settings, and expected
  controller-only behavior explicit.
- `docs/report/lab-notes/2026-09-08-rp23cnc-estop-terminal-identification.md`:
  new lab note recording the photo evidence and reasoning.
