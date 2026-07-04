# RP23CNC Ethernet Module Visual Inspection

- Date: 2026-06-09
- Related test: E-16, partial evidence only
- Device: Ethernet module supplied for the RP23CNC kit
- Evidence image:
  [`assets/2026-06-09-rp23cnc-w5500-module.jpg`](assets/2026-06-09-rp23cnc-w5500-module.jpg)

## Observations

The supplied photograph clearly shows:

- A Wiznet IC marked `W5500`.
- PCB silkscreen marked `W5500`.
- Two parallel rows of six pins, matching the connector layout required by the
  RP23U5XBB manual for its Wiz850io-format Ethernet interface.
- `Active` and `Link` indicator labels adjacent to the Ethernet connector.
- The module is not shown installed on the RP23U5XBB board.

## Result

The photographed module matches the manual's identifying requirements for the
RP23U5XBB Ethernet adapter: a W5500-based module with two six-pin rows. This
rules out the incompatible WIZ820io chipset and provides evidence against
accidentally using the differently pinned WIZ550io module.

E-16 remains incomplete because the photograph does not show the main
RP23U5XBB PCB revision or the full kit inventory. E-17 remains incomplete
because installation orientation, solder joints, continuity, and power rails
have not been inspected.

## Next inspection

Photograph the front and back of the RP23U5XBB PCB before installing the
module, including the board name, revision, Wiz850io footprint, 5V source
selector, and all supplied sockets and headers.
