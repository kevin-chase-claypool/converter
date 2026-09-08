# Lab Note: 2026-09-08 - RP23CNC ESTOP terminal identification

## Objective

Resolve the TBD RP23CNC Halt-input terminal pair in `ESTOP_TOPOLOGY.md` /
`WIRING_TABLE.md` (`SAF-004`) before landing any E-stop wiring, per the
project rule to confirm against the installed board rather than infer from
the switch drawing alone.

## Configuration

- Hardware: owner's installed Brookwood Design RP23CNC / RP23U5XBB,
  silkscreen reads `V1.01`.
- Reference: `docs/hardware/references/RP23CNC-user-manual.pdf` (board rev
  `RP23U5XBB V1.0` per its "Key Features" diagram, p.6).
- SW1: mxuteuk `HB2-BS544`, confirmed by owner photo to be a 22 mm latching
  mushroom E-stop with two independent 1/NC/2 contact blocks, matching the
  BOM entry.

## Code, commands, and configuration used

```text
pdftotext -layout "docs/hardware/references/RP23CNC-user-manual.pdf" ...
pdftoppm -png -r 600 -f 6 -l 6 "docs/hardware/references/RP23CNC-user-manual.pdf" ...
```

Used to extract manual text and render the page 6 board diagram at high
resolution for label reading. No board power, firmware, or grblHAL settings
were touched.

## Procedure

1. Extracted manual text and confirmed the "External Connections" and "Key
   Features" sections describe a `EStop, Door, Cycle/Start and Feed/Hold`
   opto-isolated input group, each with its own screw terminal.
2. Rendered the page 6 board diagram and read the labeled bottom-edge
   terminal row: `ISO 12V` -> `LIM B/A/Z/Y/X` -> `PROBE` -> `DOOR` ->
   `CY/ST` -> `FD HOLD` -> `ESTOP`, each control-input terminal carrying
   `SIG` and `GND` pins.
3. Owner supplied a photo of the switch (front, confirming red mushroom /
   yellow "EMERGENCY STOP" plate) and its rear contact block (confirming two
   independent `1 NC 2` pairs).
4. Owner supplied a photo of the installed RP23CNC board's control-input
   terminal row. Silkscreen in the photo reads (partial, left-to-right):
   `...OBE`, `DOOR SIG GND`, `CY/ST SIG GND`, `FD HOLD SIG GND`,
   `ESTOP SIG GND` — matching the manual diagram's order and labels. The
   board's own silkscreen elsewhere reads `RP23U5XBB V1.01`.

## Results

- The manual diagram (board rev V1.0) and the owner's installed board (rev
  V1.01) show the same terminal layout and labels for the control-input row.
  A one-point revision bump did not change this connector's labeling.
- `ESTOP` is confirmed as a dedicated 2-pin `SIG`/`GND` terminal, physically
  the rightmost terminal in the Grbl Control Inputs group.
- No wire was landed. No continuity check was performed on the RP23CNC side
  (E-19 covers that). SW1 NC-A/NC-B continuity was not re-verified in this
  session; it was previously confirmed part of BOM intake.

## Difficulties and corrective actions

Tried to fetch the manual directly from GitHub via the web-fetch and
in-app-browser tools first. GitHub's PDF viewer renders through a JS/canvas
viewer that returned no extractable text, and navigating straight to the raw
PDF URL was treated as a file download requiring explicit permission before
proceeding. Switched to the manual copy already saved in the repository
(`docs/hardware/references/RP23CNC-user-manual.pdf`, added under
`HW-20260704-002`) and used local `pdftotext`/`pdftoppm` instead, which
worked directly.

## Interpretation

The terminal name and pin labels are now known with reasonable confidence
(manual diagram plus matching physical board photo). This closes the
identification gap but is not itself electrical verification: the terminal
has not been continuity-checked from the RP23CNC side, no wire has been run,
and grblHAL's `$14` behavior has not been observed live.

## Decisions and next action

Proceed to E-19 as written in `ESTOP_TOPOLOGY.md`: verify SW1 NC-A/NC-B
continuity with all power removed, land NC-A across the `ESTOP` `SIG`/`GND`
pins, set `$14=6` during the live test, and confirm Halt/Reset-Unlock
behavior in ioSender before recording the `WIRING_TABLE.md` row as verified.
