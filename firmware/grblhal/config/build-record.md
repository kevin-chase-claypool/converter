# RP23U5XBB baseline build record

## 2026-08-14 Web Builder baseline

- Board: Brookwood Design RP23CNC / `RP23U5XBB` V1.01
- Builder driver: `RP2040 (Pi Pico & Pi Pico W)` with `RP_MCU=2350`
- Builder board: `BOARD_RP23U5XBB`
- Connection: native USB
- Axes: four (`X`, `Y`, `Z`, `A`); Z remains physically unwired for this machine
- Spindle 1: PWM (`SPINDLE0_ENABLE=11`)
- Probe input: disabled
- SD card: enabled with Ymodem (`SDCARD_ENABLE=2`)
- Networking: W5500, Telnet, WebSocket, and FTP enabled
- Builder configuration: [`../../../hardware/RP2040_RP23U5XBB.json`](../../../hardware/RP2040_RP23U5XBB.json)
- Firmware artifact: [`../../../hardware/firmware.uf2`](../../../hardware/firmware.uf2)
- Firmware size: 851,968 bytes
- SHA-256: `7FEE8ABC7570396155452405292AAF935A5CAB5AC10CF56AE0C84E9E4BB33A7B`

## Flash verification

Flashed through RP2350 BOOTSEL on 2026-08-14. F-01 passed over native USB on
COM9. `$I` reported grblHAL `1.1f.20260813`, board `RP23U5XBB`, four axes
`XYZA`, `RP2350@150MHz`, `WIZCHIP:W5500`, and SD-card/Ymodem plugin support.
The complete `$I` capture is preserved in the dated F-01 lab note.
