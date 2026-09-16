# Pro Micro RP2350 external power with USB CDC

- Date: 2026-09-16
- Question: Can the SparkFun Pro Micro RP2350 remain powered from the
  toolhead 5 V rail while its USB-C port is connected to the PC for commands
  and telemetry?
- Scope: primary SparkFun, Raspberry Pi, and Arduino-Pico documentation;
  no bench result yet.

## Conclusion

The recommended **lowest-change calibration arrangement** is the existing
USB-to-TTL service adapter for the Pro Micro and native USB for the Pico 2.
This gives the PC two USB COM ports without altering the externally powered
Pro Micro's working power arrangement:

1. Pico USB CDC carries every timestamped CS1238/reference record at the
   measured CS1238 rate.
2. The already bench-verified USB-to-TTL adapter carries only Pro Micro
   command/acknowledgement and low-rate actuator status at 115200 baud.

Do not put CS1238 samples on the Pro Micro UART. At 115200 8N1, its maximum
payload is about 11.52 kB/s; a human-readable 640-SPS CSV stream is above that
budget. The Pico stream is the force-data authority, while the Pro Micro log
only records commanded motion events.

Direct Pro Micro USB-C CDC is a viable **later simplification**, not the first
fixture configuration. SparkFun documents external `RAW` power and the
schematic shows USB VBUS reaching the regulator through a fuse and Schottky
diode, so a standard data cable may coexist with external power. Nevertheless,
the exact installed supply connection and cable must pass the stated voltage
test before that path replaces the already working service adapter.

Do not cut VBUS or use a “data-only” cable as the first solution. USB device
attach/enumeration depends on the host VBUS/attach sequence, and the board
documentation does not promise enumeration with VBUS absent.

## Evidence

1. SparkFun's official hardware overview says the USB-C connector is the
   primary power/programming interface, USB-C voltage is regulated to 3.3 V,
   and RAW is a dedicated external supply input limited to 5.3 V because it
   also feeds the WS2812 LED: <https://docs.sparkfun.com/SparkFun_Pro_Micro_RP2350/hardware_overview/>.
2. SparkFun's released schematic labels the connector nets `VBUS`, `D-`, and
   `D+`; it shows `V_USB -> F1 (6 V, 0.5 A) -> D2 (Schottky) -> U1 IN`, with
   regulator output feeding the board: <https://docs.sparkfun.com/SparkFun_Pro_Micro_RP2350/assets/board_files/SparkFun_ProMicro_RP2350.pdf>.
3. The official RP2350 datasheet requires the USB PHY supply to be present even
   when USB is unused, so externally powering the board does not inherently
   disable the USB peripheral: <https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008373-DS-2-rp2350-datasheet.pdf?disposition=inline>.
4. Arduino-Pico's official USB documentation states that the default Pico SDK
   stack automatically provides a USB-based `Serial` port. It also documents
   `USB.connect()` as the software attach/rescan mechanism and explicitly notes
   that it is safe to call while self-powered: <https://github.com/earlephilhower/arduino-pico/blob/master/docs/usb.rst>.
5. Raspberry Pi's official Pico 2 datasheet documents USB VBUS as the connector
   input and diode-OR power behavior; it cautions against tying USB VBUS sources
   together. This supports checking for board-level isolation rather than
   assuming that two 5 V supplies may be shorted: <https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf>.

## Minimal test procedure

With the toolhead supply off, inspect the board/schematic and confirm the
external input is RAW (not a 3.3 V pin). Power the Pro Micro from the regulated
5 V rail, connect a standard USB-C data cable, and measure the PC cable VBUS
relative to board ground before and after connection. Confirm that the board
enumerates as a USB serial device and that the external 5 V rail does not rise
when the board is unpowered and only USB is connected. Abort if either supply
backfeeds or the board input exceeds 5.3 V.

For this calibration, send only low-rate motion commands/acknowledgements over
the existing USB-to-TTL/Pro Micro `Serial2` link; leave high-rate CS1238
acquisition and both sensor timestamps on the Pico 2 USB stream.

## Open verification

The cited documents establish the intended power topology and USB CDC support,
but they do not certify every cable, regulator revision, or assembled-board
backfeed path. A powered continuity/voltage check and one enumeration test are
still required before connecting the PC and toolhead supply simultaneously.
