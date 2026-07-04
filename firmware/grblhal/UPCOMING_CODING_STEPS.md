# RP23U5XBB Ethernet and grblHAL Upcoming Coding Steps

Reviewed on 2026-06-09 against the Brookwood Design
`RP23CNC User Manual`, covering RP23U5XBB versions 1.0 and 1.01, the separate
assembly instructions, and the current project interface documents.

Board creator Phil Barrett maintains the canonical hardware repository at
[`phil-barrett/RP23CNC`](https://github.com/phil-barrett/RP23CNC). Use that
repository for the latest manual, assembly instructions, schematics, board
revision information, and related hardware files.

This is the implementation sequence for the received board. It is a plan, not a
record of completed hardware or firmware verification.

## Board identity and Ethernet hardware gate

The received board has been photographically identified as
`RP23CNC RP23U5XBB V1.01`. Use the `RP23U5XBB` Web Builder board target and
retain the exact V1.01 revision in build and wiring records.

Before firmware work:

1. Complete the remaining E-16 inventory: the
   [main-board inspection](../../docs/report/lab-notes/2026-06-09-rp23u5xbb-v1.01-board-inspection.md)
   confirms V1.01 and installed connectors, but missing or damaged kit items
   still need an explicit inventory result.
2. The supplied module photograph confirms a Wiznet `W5500` IC and two six-pin
   rows, matching the manual's Wiz850io-format requirement. Preserve the
   [inspection note](../../docs/report/lab-notes/2026-06-09-rp23cnc-w5500-module-inspection.md)
   as partial E-16 evidence.
3. Do not substitute a `WIZ550io`; it uses the W5500 but has an incompatible
   pinout. Do not use a WIZ820io.
4. Install the two 1x6 sockets, tack one pin on each, verify seating and
   orientation, then solder the remaining pins.
5. Complete test E-17: the overview photographs are not sufficient to certify
   all joints. Inspect under magnification and meter-check for bridges, opens,
   reversed parts, and power-rail shorts before applying power.

If the Wiz850io is soldered directly rather than socketed, the manual requires
removing the obstructing 5V Source Select header and selecting the 5V source
with exactly one bottom-side solder jumper. The project should use sockets
unless vibration testing later justifies direct soldering.

## Stage 1: create a reproducible baseline build

Use the grblHAL Web Builder for the first working firmware. Do not begin with a
custom fork.

1. Select driver `RP2040 (Pi Pico and Pi Pico W)`.
2. Select board `RP23U5XBB`.
3. Configure four axes so the firmware exposes `X`, `Y`, `Z`, and `A`.
   This machine uses X, Y, and A; Z remains unconnected and disabled in the
   machine configuration unless later needed.
4. Enable the SD-card option with `Ymodem`, as recommended by the manual.
5. Save the Web Builder board configuration before downloading the UF2.
6. Record the builder date, selected options, downloaded filename, and SHA-256
   in `config/build-record.md`.

Acceptance:

- A saved builder configuration can regenerate the same feature set.
- The UF2 and its checksum are archived without credentials or local network
  secrets.

## Stage 2: enable Ethernet in the build

In the Web Builder `Network/WebUI` panel:

1. Select `Wiz550io (W5500)`. This builder label is correct for the installed
   Wiz850io-format W5500 module.
2. Enable the Telnet server.
3. Enable the WebSocket server.
4. Enable the FTP server only for initial compatibility with the manual.
   Disable it later if it is not needed for the selected sender or SD workflow.
5. Keep DHCP enabled for first bring-up.

Do not expose the controller directly to the public internet. Treat Telnet and
FTP as trusted-LAN services without transport security.

Acceptance:

- Boot output identifies Ethernet as enabled and reports `WIZCHIP: W5500`.
- The DHCP-assigned address is recorded as test evidence, not committed as a
  permanent project constant.

## Stage 3: flash and establish USB recovery

1. Put the RP2350 into BOOTSEL mode: hold RESET, hold BOOT, release RESET, then
   release BOOT.
2. Copy the generated UF2 to the exposed RP2350 drive.
3. Connect by USB first and capture the complete boot banner.
4. Confirm the reported grblHAL version, RP23U5XBB board target, enabled axis
   count, Ethernet support, and W5500 detection.
5. Save this evidence in `config/build-record.md`.

USB remains the recovery and initial-configuration path even when Ethernet is
the normal machine transport.

## Stage 4: first-run control settings

The manual warns that the board commonly starts in Alarm because E-stop, Feed
Hold, and Cycle Start default to normally closed behavior. For a temporary
unwired bench baseline, set `$14=70`, reboot, and record why it was used.

For the final machine:

- Prefer normally closed E-stop, Feed Hold, Cycle Start, and limit circuits.
- Replace temporary inversion values with settings matched to the verified
  wiring.
- Configure a four-axis build/limit mask so A is available with X/Y, while the
  Z axis slot remains unused and unwired.
- Determine `$4` stepper-enable inversion from unpowered output testing; do not
  copy `$4=15` without test F-03 evidence.
- Keep drivers, motors, spindle/toolhead, and mechanics disconnected for the
  parser and output-baseline tests.

## Stage 5: prove Ethernet transport

1. Connect the board to a DHCP-capable private network and connect by USB.
2. Verify link activity on the Wiz850io.
3. Read the boot output and record the assigned IP address.
4. Close the USB sender session before opening the Ethernet session.
5. Connect the sender to the recorded address using Telnet.
6. Confirm the console reports `[NETCON: Telnet]`.
7. Send status and settings queries and verify responses are identical over USB
   and Ethernet.
8. Reserve the DHCP lease in the router. Do not hard-code an address until the
   network design requires it.
9. Document the sender, connection procedure, enabled services, and recovery
   path in `config/ethernet.md`.

Add a dedicated firmware verification row for Ethernet to the test plan when
the physical board is ready for testing. The evidence should include boot
banner, W5500 detection, assigned address, Telnet connection, and a short
command exchange.

## Stage 6: configure the plotter contract

After the baseline transport works:

1. Save a complete initial `$` settings dump in `config/machine-settings.md`.
2. Configure X/Y steps per millimeter from measured mechanics and microstepping.
3. Configure A steps per unit as motor steps per degree:

   ```text
   A steps/degree = motor full-steps/revolution * microsteps / 360
   ```

   Do not apply the 12:1 bed ratio again; the converter already emits motor
   shaft degrees.
4. Set conservative per-axis rates and accelerations before attaching
   mechanics.
5. Verify the converter subset: `G21`, `G90`, `G0/G1 X Y A F`, `M3`, `M5`,
   `G4 P...`, and `M2`.
6. Verify STEP/DIR/ENABLE signals without powered drivers.
7. Verify limit/control input polarity.
8. Verify the selected spindle/tool output pin state is fail-safe for the
   future toolhead: `M3` = ENGAGE and `M5` = LIFT/OFF.
9. For homing and bed calibration, keep grblHAL responsible for motion and
   digital limit/home handling. X/Y home from physical switches, and normal A
   homing uses the validated switch-like `A_HOME` signal from the
   RP2040/TMAG5273 adapter. Use the setup-calibration process in
   [`HOMING_AND_MAGNETIC_CALIBRATION.md`](HOMING_AND_MAGNETIC_CALIBRATION.md)
   to determine thresholds, hysteresis, offsets, and repeatability before
   considering a custom grblHAL plugin.

## Stage 7: decide what code is actually needed

No custom motion-control code is currently justified. The expected work is
configuration, reproducibility records, and tests.

Write custom grblHAL code only after the baseline proves a specific gap:

- A plugin may later replace fixed `G4` delays with a `CONTACT_READY` or
  `TOOL_FAULT` handshake.
- A plugin may later participate in magnetic calibration only if the
  RP2040/TMAG5273 adapter plus sender/setup-calibration process proves an
  actual grblHAL limitation.
- Toolhead force control should remain on a separate MCU unless the RP2350 pin
  audit and timing measurements prove a supported plugin/core-1 design is
  maintainable.
- Any plugin must preserve reset, E-stop, and watchdog behavior that defaults
  the toolhead to LIFT/OFF.

## Files to create during bring-up

| File | Trigger |
|---|---|
| `config/build-record.md` | First generated UF2 |
| `config/ethernet.md` | First successful DHCP/Telnet session |
| `config/machine-settings.md` | First saved settings dump |
| `config/pin-map.md` | Board revision and signals verified against schematic and meter tests |
| `docs/report/lab-notes/YYYY-MM-DD-rp23cnc-bring-up.md` | First powered board session |

## Source references

- [RP23U5XBB board page](https://www.grbl.org/rp23u5xbb)
- [Phil Barrett's canonical RP23CNC repository](https://github.com/phil-barrett/RP23CNC)
- [RP23CNC user manual](https://github.com/phil-barrett/RP23CNC/blob/main/Documentation/user%20manual.pdf)
  (archived at
  [`../../docs/hardware/references/RP23CNC-user-manual.pdf`](../../docs/hardware/references/RP23CNC-user-manual.pdf))
- [RP23U5XBB assembly instructions](https://github.com/phil-barrett/RP23CNC/blob/main/Documentation/RP23U5XBB%20Assembly%20Instructions.pdf)
  (archived at
  [`../../docs/hardware/references/RP23U5XBB-assembly-instructions.pdf`](../../docs/hardware/references/RP23U5XBB-assembly-instructions.pdf))
- [RP2040/RP2350 grblHAL driver](https://github.com/grblHAL/RP2040)
