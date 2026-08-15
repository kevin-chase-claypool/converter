# Lab Note: 2026-08-14 - F-01 RP23CNC grblHAL baseline boot

## Objective

Verify that the generated RP23U5XBB grblHAL firmware flashes, boots, and
identifies the expected controller features over native USB.

## Configuration

- Controller: Brookwood Design RP23CNC / RP23U5XBB V1.01
- Firmware: `hardware/firmware.uf2`, SHA-256
  `7FEE8ABC7570396155452405292AAF935A5CAB5AC10CF56AE0C84E9E4BB33A7B`
- USB serial: COM9, ioSender 2.0.47
- External connections: USB; isolated-input 12 V only for clearing the
  first-run control alarm; main 12 V, drivers, motors, Ethernet, and PC817
  controller-side harness disconnected

## Code, commands, and configuration used

```text
$I
$HELP
```

## Procedure

1. Completed E-17 inspection and no-short checks.
2. Entered RP2350 BOOTSEL mode and copied `firmware.uf2` to the USB mass-storage
   drive.
3. Connected ioSender to COM9 at 115200 baud.
4. Sent `$I` through the MDI command field.

## Results

```text
$I
[VER:1.1f.20260813:]
[OPT:VNMSL,100,1024,4,0]
[AXS:4:XYZA]
[NEWOPT:ENUMS,RT+,NOPROBE,ES,REBOOT,TC,SED,ETH,YM,SD]
[FIRMWARE:grblHAL]
[SIGNALS:HSE]
[NVS STORAGE:*FLASH 4K]
[FREE MEMORY:372K]
[DRIVER:RP2350@150MHz]
[DRIVER VERSION:260608]
[DRIVER OPTIONS:SDK_2.1.0]
[BOARD:RP23U5XBB]
[AUX IO:6,2,0,0]
[WIZCHIP:W5500]
[MAC:00:08:dc:12:34:56]
[IP:]
[PLUGIN:Bootloader Entry v0.01]
[PLUGIN:FS stream v1.14]
[PLUGIN:FS macro plugin v0.24]
[PLUGIN:SDCARD v1.28]
```

- F-01 passed: native USB communication, RP2350 driver, RP23U5XBB board map,
  four-axis XYZA configuration, W5500 detection, and SD/Ymodem capabilities
  match the build record.
- `ALARM:10` was present with unwired safety/control inputs. This is expected
  for the USB-only baseline and does not invalidate the firmware identity test.
- Blank IP is expected because Ethernet was not connected to a DHCP network.

## Difficulties and corrective actions

- Initial `$$` requests and the temporary console command `$14=70` returned
  `error:79 - Not allowed while critical event is active.` The boot report
  showed `SIGNALS:HSE`, meaning the unwired Feed Hold, Cycle Start, and E-stop
  control inputs were active.
- This is the documented first-run behavior for the board's opto-isolated 12 V
  control inputs. The RP23CNC manual directs initial inversion through
  ioSender's **Settings: Grbl** control-signals editor, then a reboot, rather
  than attempting a console setting write while the critical event is active.

## Interpretation

The controller baseline is operational and can enter `IDLE` with only the
isolated-input supply attached. No motion or controller I/O has been tested;
all machine outputs and the PC817 controller-side harness remain detached.

## Alarm-clear acceptance result

1. Supplied the board's `ISO 12V` input from the bench supply while leaving the
   main 12 V input and all machine-load wiring disconnected.
2. Used ioSender's **Settings: Grbl** control-signals editor to invert the
   unwired Feed Hold, Cycle Start, and E-stop inputs, saved the setting, and
   rebooted.
3. Clicked **Unlock** in ioSender.

The status changed from `ALARM:10` to `IDLE` and ioSender reported
`Caution: Unlocked`. This verifies that the first-run alarm was caused by the
unpowered/uninverted opto-isolated control inputs, not a firmware fault.

## Post-unlock command-channel check

The commands below were sent in ioSender while `IDLE`:

```text
$$
$HELP
$HELP Settings
```

`$$` was echoed to the console but returned no settings listing. `$HELP`
returned the available help topics, including `Settings`, `Control signals`,
and all four axis groups. This proves the USB command path and normal command
parser are working; the missing report is specific to this build's `$$`
response or the sender's rendering of it. Use **Settings: Grbl → Reload** as
the configuration-reading path until that behavior is explained.

`$HELP Settings` returned the complete list of supported setting IDs and
descriptions, ending in `ok`. It is a help listing rather than a current-value
dump, which confirms the settings subsystem is present but does not replace a
snapshot from ioSender's settings UI.

## Decisions and next action

Capture the complete initial `$$` settings dump. Perform F-03/F-04 with outputs
and inputs unpowered/unconnected, followed by F-05 to establish actual ENA and
Aux0 states.
