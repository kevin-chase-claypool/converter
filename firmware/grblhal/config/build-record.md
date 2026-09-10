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

## 2026-09-10 homing candidate

- Builder configuration: [`../../../hardware/RP2040_RP23U5XBB_homing_candidate.json`](../../../hardware/RP2040_RP23U5XBB_homing_candidate.json)
- Firmware artifact: [`../../../hardware/firmware-homing-candidate.uf2`](../../../hardware/firmware-homing-candidate.uf2)
- Firmware size: 889,856 bytes
- SHA-256: `892799841E6262556D380594CF909FE8A40284BC6FA52E798102BFEC36276DC9`
- Added candidate capabilities: `PROBE_ENABLE=1`, NGC parameters, and NGC
  expressions. The known-good baseline artifact remains unchanged.
- Installed boot report: grblHAL `1.1f.20260908`; `XYZA`; `[SIGNALS:HSEP]`;
  `[NEWOPT:ENUMS,RT+,HOME,ES,REBOOT,EXPR,TC,SED,ETH,YM,SD]`; `PRB` mapped to
  pin 7; `Aux out 0,P0` mapped to pin 36.
- F-08 used `$6=1` for the installed normally-open PRB sink, then restored
  `$20=1` and `G90` at completion. Full evidence is in
  [`../../../docs/report/lab-notes/2026-09-10-e-18-motor-inert-p100-handshake.md`](../../../docs/report/lab-notes/2026-09-10-e-18-motor-inert-p100-handshake.md).

## 2026-09-06 unloaded motion commissioning snapshot

The installed controller and TB6600 signal paths passed their documented
bring-up checks. The Y-axis rate ramp completed its stepped bidirectional test
without reported skipped steps, stalls, or jerking. The X-axis completed five
matched 50 mm forward/reverse moves at `F1500` and returned exactly to its
reference mark. The operator selected the following preliminary X/Y settings
for continued commissioning:

| Setting | Value | Scope |
|---|---:|---|
| `$100` | `80.00000` steps/mm | Current owner-caliper-verified X setting; earlier `79.71303` correction superseded |
| `$101` | `80.000000` steps/mm | Y 100 mm M-03 check passed |
| `$110` | `1500` mm/min | Preliminary unloaded maximum-rate setting |
| `$111` | `1500` mm/min | Preliminary unloaded maximum-rate setting |
| `$120` | `500` mm/sec^2 | Preliminary unloaded acceleration setting |
| `$121` | `500` mm/sec^2 | Preliminary unloaded acceleration setting |
| `$130` | `455.000` mm | Conservative observed-safe X software envelope |
| `$131` | `446.000` mm | Conservative observed-safe Y software envelope |
| `$133` | `0.000` deg | Continuous A bed: no finite maximum travel |
| `$20` / `$21` | `1` / `0` | X/Y soft limits enabled; hard-limit alarms remain disabled |
| `$40` | `1` | Soft limits also apply to jogging |
| `$22` / `$23` | `3` / `2` | X/Y homing enabled with single-axis diagnostics; Y homes negative |
| `$24` / `$25` / `$27` | `50` / `500` mm/min / `10.000` mm | Locate, seek, and pull-off settings; 10 mm intentionally clears nearby switch wiring |
| `$43` / `$44` / `$45-$47` | `1` / `XY` / `none` | One XY-only homing phase; Z and A excluded |

These values are not a final pen-loaded plotting limit. X/Y physical homing
and a pen-free converter-generated return test passed, but explicit
near-boundary soft-limit rejection/recovery, G54 magnetic registration, and
loaded toolhead validation remain. Do not assign a finite A soft limit.
