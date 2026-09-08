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

# Identify the RP23CNC ESTOP screw terminal

## Summary

The RP23CNC's dedicated Halt input terminal, previously recorded as TBD, is
now identified: a 2-pin `ESTOP` screw terminal (`SIG` / `GND`), the rightmost
terminal in the "Grbl Control Inputs" group on the RP23U5XBB board, after
`DOOR`, `CY/ST`, and `FD HOLD`. No wire has been landed and E-19 has not been
performed; only the terminal identification is resolved.

## Reason

`HW-20260814-005` locked the decision to use SW1 NC-A on the RP23CNC's
dedicated Halt input, but deliberately left the exact terminal pair blank
pending agreement between the manual and the installed board's silkscreen.
The owner asked to move forward on wiring the E-stop, which required closing
that TBD first.

## Implementation

No physical wiring changed. This note records the terminal identification
only:

- The RP23CNC user manual's "Key Features" board diagram
  (`docs/hardware/references/RP23CNC-user-manual.pdf`, p.6, board rev
  RP23U5XBB V1.0) labels the terminal `ESTOP` with `SIG`/`GND` pins.
- A photo of the owner's installed board (rev `RP23U5XBB V1.01` per its own
  silkscreen) shows the same terminal row and labels in the same position,
  confirming the manual's diagram matches the physical unit.
- `docs/hardware/ESTOP_TOPOLOGY.md` and `docs/hardware/WIRING_TABLE.md`
  (`SAF-004`) were updated to name the terminal instead of TBD, and both still
  state the connection is planned/identified, not landed or verified.

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
  and updated the net topology and E-19 step 2 to name the `ESTOP`
  `SIG`/`GND` terminal instead of TBD.
- `docs/hardware/WIRING_TABLE.md`: updated `SAF-004`'s target terminal and
  notes.
- `docs/report/lab-notes/2026-09-08-rp23cnc-estop-terminal-identification.md`:
  new lab note recording the photo evidence and reasoning.
